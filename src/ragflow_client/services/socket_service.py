"""
Socket.IO WebSocket service with reconnection logic.

Handles real-time bi-directional communication with the RAGFlow backend,
including authentication, exponential backoff reconnection, and event routing.
"""

import asyncio
from typing import TYPE_CHECKING, Any

import socketio
from loguru import logger

if TYPE_CHECKING:
    from ragflow_client.core.bus import EventBus
    from ragflow_client.utils.config import Settings

from ragflow_client.core.bus import Event, EventPayload


class SocketService:
    """
    Socket.IO client service with automatic reconnection.
    
    Features:
    - Authentication with API key and optional email
    - Exponential backoff reconnection (1s, 2s, 4s... up to max_delay)
    - Event bridging to internal event bus
    - Configurable ping interval/timeout matching server config
    
    Example:
        service = SocketService(settings, event_bus)
        await service.connect()
    """
    
    def __init__(self, settings: "Settings", bus: "EventBus") -> None:
        """
        Initialize the socket service.
        
        Args:
            settings: Application settings with connection configuration.
            bus: Internal event bus for routing events.
        """
        self.settings = settings
        self.bus = bus
        self._logger = logger.bind(component="SocketService")
        
        # Reconnection state
        self._reconnect_delay = 1.0
        self._connected = False
        self._should_reconnect = True
        
        # Create Socket.IO client
        self._sio = socketio.AsyncClient(
            reconnection=False,  # We handle reconnection ourselves
            logger=False,
            engineio_logger=False,
        )
        
        # Register event handlers
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Setup Socket.IO event handlers."""
        
        @self._sio.event
        async def connect() -> None:
            self._connected = True
            self._reconnect_delay = 1.0  # Reset backoff on successful connect
            self._logger.info("Connected to server")
            
            await self.bus.publish(Event(
                name="socket:connected",
                source="SocketService",
            ))
        
        @self._sio.event
        async def disconnect() -> None:
            self._connected = False
            self._logger.warning("Disconnected from server")
            
            await self.bus.publish(Event(
                name="socket:disconnected",
                source="SocketService",
            ))
        
        @self._sio.event
        async def connect_error(data: Any) -> None:
            self._logger.error(f"Connection error: {data}")
            self._connected = False
            
            await self.bus.publish(Event(
                name="socket:error",
                payload={"error": str(data)},
                source="SocketService",
            ))
        
        # Handle server notifications (document conversion requests, etc.)
        @self._sio.on("notification")
        async def on_notification(data: dict[str, Any]) -> None:
            self._logger.debug(f"Received notification: {data}")
            
            notification_type = data.get("type", "unknown")
            
            # Route to appropriate event
            await self.bus.publish(Event(
                name=f"server:{notification_type}",
                payload=data,
                source="SocketService",
            ))
        
        # Handle document conversion requests specifically
        @self._sio.on("doc:convert:request")
        async def on_doc_convert_request(data: dict[str, Any]) -> None:
            self._logger.info(f"Received document conversion request: {data.get('id', 'unknown')}")
            
            await self.bus.publish(Event(
                name="doc:convert",
                payload=data,
                source="SocketService",
            ))
        
        # Handle generic messages
        @self._sio.on("message")
        async def on_message(data: Any) -> None:
            self._logger.debug(f"Received message: {data}")
            
            await self.bus.publish(Event(
                name="server:message",
                payload={"data": data} if not isinstance(data, dict) else data,
                source="SocketService",
            ))
    
    async def connect(self) -> None:
        """
        Connect to the WebSocket server with automatic reconnection.
        
        This method runs indefinitely, handling reconnection with
        exponential backoff until shutdown is requested.
        """
        self._logger.info(f"Connecting to {self.settings.websocket_url}...")
        
        while self._should_reconnect:
            try:
                # Prepare auth payload
                auth = {
                    "apiKey": self.settings.websocket_api_key,
                }
                if self.settings.user_email:
                    auth["email"] = self.settings.user_email
                
                # Connect with auth
                await self._sio.connect(
                    self.settings.websocket_url,
                    auth=auth,
                    transports=["websocket"],
                    wait_timeout=10,
                )
                
                # Wait until disconnected
                await self._sio.wait()
                
            except socketio.exceptions.ConnectionError as e:
                self._logger.warning(f"Connection failed: {e}")
            except asyncio.CancelledError:
                self._logger.info("Connection cancelled")
                break
            except Exception as e:
                self._logger.exception(f"Unexpected error: {e}")
            
            if not self._should_reconnect:
                break
            
            # Exponential backoff
            self._logger.info(f"Reconnecting in {self._reconnect_delay:.1f}s...")
            await asyncio.sleep(self._reconnect_delay)
            self._reconnect_delay = min(
                self._reconnect_delay * 2,
                self.settings.reconnect_max_delay
            )
    
    async def disconnect(self) -> None:
        """Disconnect from the server and stop reconnection attempts."""
        self._should_reconnect = False
        
        if self._connected:
            try:
                await self._sio.disconnect()
            except Exception as e:
                self._logger.warning(f"Error during disconnect: {e}")
        
        self._logger.info("Socket service stopped")
    
    async def emit(self, event: str, data: Any = None) -> None:
        """
        Emit an event to the server.
        
        Args:
            event: Event name to emit.
            data: Data payload to send.
        """
        if not self._connected:
            self._logger.warning(f"Cannot emit '{event}': not connected")
            return
        
        try:
            await self._sio.emit(event, data)
            self._logger.debug(f"Emitted '{event}'")
        except Exception as e:
            self._logger.error(f"Failed to emit '{event}': {e}")
    
    async def send_progress(self, job_id: str, progress: int, status: str = "processing") -> None:
        """
        Send job progress update to the server.
        
        Args:
            job_id: Job identifier.
            progress: Progress percentage (0-100).
            status: Current job status.
        """
        await self.emit("doc:convert:progress", {
            "id": job_id,
            "progress": progress,
            "status": status,
        })
    
    async def send_result(self, job_id: str, success: bool, result: Any = None, error: str | None = None) -> None:
        """
        Send job result to the server.
        
        Args:
            job_id: Job identifier.
            success: Whether the job completed successfully.
            result: Job result data (if successful).
            error: Error message (if failed).
        """
        await self.emit("doc:convert:result", {
            "id": job_id,
            "success": success,
            "result": result,
            "error": error,
        })
    
    @property
    def is_connected(self) -> bool:
        """Check if currently connected to the server."""
        return self._connected
