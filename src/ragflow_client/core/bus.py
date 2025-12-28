"""
Internal async event bus using asyncio.Queue.

Implements a pub/sub pattern for decoupling network events from feature logic.
Event naming follows the `feature:action` format (e.g., `doc:convert`, `sys:shutdown`).
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Self
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, Field


# Type aliases (PEP 695)
type EventHandler = Callable[["Event"], Coroutine[Any, Any, None]]
type EventName = str


class EventPayload(BaseModel):
    """Base class for event payloads with Pydantic validation."""
    
    class Config:
        extra = "allow"


@dataclass
class Event:
    """
    Represents an event in the internal bus.
    
    Attributes:
        name: Event name in `feature:action` format.
        payload: Event data (Pydantic model for validation).
        id: Unique identifier for this event.
        timestamp: When the event was created.
        source: Optional source identifier (e.g., component name).
    """
    
    name: EventName
    payload: EventPayload | dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = ""
    
    def __str__(self) -> str:
        return f"Event({self.name}, id={self.id.hex[:8]}, source={self.source or 'unknown'})"


class EventBus:
    """
    Async event bus using asyncio.Queue for non-blocking event dispatch.
    
    Features:
    - Pub/Sub pattern with typed handlers
    - Wildcard subscriptions (e.g., `doc:*` for all doc events)
    - Event history for debugging
    - Graceful shutdown support
    
    Example:
        bus = EventBus()
        
        async def on_convert(event: Event):
            print(f"Converting: {event.payload}")
        
        bus.subscribe("doc:convert", on_convert)
        await bus.publish(Event(name="doc:convert", payload={"file": "test.pdf"}))
        await bus.start()
    """
    
    def __init__(self, max_history: int = 100) -> None:
        """
        Initialize the event bus.
        
        Args:
            max_history: Maximum number of events to keep in history.
        """
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._handlers: dict[EventName, list[EventHandler]] = defaultdict(list)
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._history: list[Event] = []
        self._max_history = max_history
        self._logger = logger.bind(component="EventBus")
    
    def subscribe(self, event_name: EventName, handler: EventHandler) -> Self:
        """
        Subscribe a handler to an event.
        
        Args:
            event_name: Event name to subscribe to (supports wildcards like `doc:*`).
            handler: Async function to call when event is published.
            
        Returns:
            Self for method chaining.
        """
        self._handlers[event_name].append(handler)
        self._logger.debug(f"Subscribed handler to '{event_name}'")
        return self
    
    def unsubscribe(self, event_name: EventName, handler: EventHandler) -> Self:
        """
        Unsubscribe a handler from an event.
        
        Args:
            event_name: Event name to unsubscribe from.
            handler: The handler function to remove.
            
        Returns:
            Self for method chaining.
        """
        if event_name in self._handlers:
            try:
                self._handlers[event_name].remove(handler)
                self._logger.debug(f"Unsubscribed handler from '{event_name}'")
            except ValueError:
                pass
        return self
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event to the bus.
        
        Args:
            event: The event to publish.
        """
        await self._queue.put(event)
        self._logger.debug(f"Published {event}")
    
    def publish_sync(self, event: Event) -> None:
        """
        Publish an event synchronously (for use in non-async contexts).
        
        Args:
            event: The event to publish.
        """
        self._queue.put_nowait(event)
        self._logger.debug(f"Published (sync) {event}")
    
    async def start(self) -> None:
        """Start the event bus dispatcher loop."""
        if self._running:
            self._logger.warning("Event bus already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._dispatch_loop())
        self._logger.info("Event bus started")
    
    async def stop(self) -> None:
        """Stop the event bus gracefully."""
        if not self._running:
            return
        
        self._running = False
        
        # Send shutdown event to unblock the queue
        await self.publish(Event(name="sys:shutdown", source="EventBus"))
        
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._logger.warning("Event bus shutdown timed out, cancelling...")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
        
        self._logger.info("Event bus stopped")
    
    async def _dispatch_loop(self) -> None:
        """Main dispatch loop processing events from the queue."""
        while self._running:
            try:
                event = await self._queue.get()
                
                # Add to history
                self._history.append(event)
                if len(self._history) > self._max_history:
                    self._history.pop(0)
                
                # Skip shutdown event processing
                if event.name == "sys:shutdown":
                    continue
                
                # Find matching handlers
                handlers = self._get_matching_handlers(event.name)
                
                if not handlers:
                    self._logger.debug(f"No handlers for {event}")
                    continue
                
                # Execute handlers concurrently
                await asyncio.gather(
                    *(self._safe_call(handler, event) for handler in handlers),
                    return_exceptions=True,
                )
                
            except asyncio.CancelledError:
                self._logger.debug("Dispatch loop cancelled")
                break
            except Exception as e:
                self._logger.exception(f"Error in dispatch loop: {e}")
    
    def _get_matching_handlers(self, event_name: EventName) -> list[EventHandler]:
        """
        Get all handlers that match an event name (including wildcards).
        
        Args:
            event_name: The event name to match.
            
        Returns:
            List of matching handler functions.
        """
        handlers: list[EventHandler] = []
        
        # Exact match
        handlers.extend(self._handlers.get(event_name, []))
        
        # Wildcard match (e.g., `doc:*` matches `doc:convert`)
        if ":" in event_name:
            prefix = event_name.split(":")[0]
            wildcard = f"{prefix}:*"
            handlers.extend(self._handlers.get(wildcard, []))
        
        # Global wildcard
        handlers.extend(self._handlers.get("*", []))
        
        return handlers
    
    async def _safe_call(self, handler: EventHandler, event: Event) -> None:
        """
        Safely call a handler, catching any exceptions.
        
        Args:
            handler: The handler function to call.
            event: The event to pass to the handler.
        """
        try:
            await handler(event)
        except Exception as e:
            self._logger.exception(
                f"Handler error for {event.name}: {e}"
            )
    
    @property
    def history(self) -> list[Event]:
        """Get the event history (read-only copy)."""
        return list(self._history)
    
    @property
    def is_running(self) -> bool:
        """Check if the event bus is running."""
        return self._running


# Global event bus instance
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.
    
    Returns:
        The singleton EventBus instance.
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
