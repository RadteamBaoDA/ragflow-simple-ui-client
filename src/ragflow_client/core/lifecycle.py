"""
Application lifecycle management.

Handles signal processing, graceful shutdown, and resource cleanup coordination.
Ensures proper handling of asyncio.CancelledError for clean shutdown.
"""

import asyncio
import signal
import sys
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from ragflow_client.utils.config import Settings


class LifecycleManager:
    """
    Manages the application lifecycle including startup, shutdown, and signal handling.
    
    Coordinates all async components (event bus, socket service, feature workers)
    and ensures graceful shutdown with proper resource cleanup.
    """
    
    def __init__(self, settings: "Settings") -> None:
        """
        Initialize the lifecycle manager.
        
        Args:
            settings: Application settings.
        """
        self.settings = settings
        self._shutdown_event = asyncio.Event()
        self._tasks: list[asyncio.Task[None]] = []
        self._logger = logger.bind(component="Lifecycle")
    
    async def run(self) -> None:
        """
        Run the main application loop.
        
        This is the primary entry point for the async application.
        Sets up signal handlers, starts all services, and waits for shutdown.
        """
        self._logger.info("Starting RAGFlow Client...")
        
        # Setup signal handlers
        self._setup_signals()
        
        try:
            # Import and initialize components
            from ragflow_client.core.bus import get_event_bus
            from ragflow_client.services.socket_service import SocketService
            from ragflow_client.features.doc_converter.worker import DocConverterWorker
            
            # Get the event bus
            bus = get_event_bus()
            
            # Initialize services
            socket_service = SocketService(self.settings, bus)
            doc_worker = DocConverterWorker(bus)
            
            # Start the event bus
            await bus.start()
            
            # Register feature workers
            await doc_worker.start()
            
            # Connect to WebSocket server
            self._tasks.append(
                asyncio.create_task(socket_service.connect(), name="socket_service")
            )
            
            self._logger.info("All services started, waiting for shutdown signal...")
            
            # Wait for shutdown
            await self._shutdown_event.wait()
            
        except asyncio.CancelledError:
            self._logger.info("Application cancelled")
        except Exception as e:
            self._logger.exception(f"Application error: {e}")
        finally:
            await self._shutdown()
    
    async def _shutdown(self) -> None:
        """Perform graceful shutdown of all components."""
        self._logger.info("Initiating graceful shutdown...")
        
        # Cancel all running tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
        
        # Stop the event bus
        try:
            from ragflow_client.core.bus import get_event_bus
            bus = get_event_bus()
            await bus.stop()
        except Exception as e:
            self._logger.warning(f"Error stopping event bus: {e}")
        
        self._logger.info("Shutdown complete")
    
    def _setup_signals(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        if sys.platform == "win32":
            # Windows: Use signal module directly
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        else:
            # Unix: Use asyncio's signal handling
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self._async_signal_handler(s))
                )
    
    def _signal_handler(self, signum: int, frame: object) -> None:
        """Synchronous signal handler (Windows)."""
        self._logger.info(f"Received signal {signum}")
        self._shutdown_event.set()
    
    async def _async_signal_handler(self, signum: signal.Signals) -> None:
        """Async signal handler (Unix)."""
        self._logger.info(f"Received signal {signum.name}")
        self._shutdown_event.set()
    
    def request_shutdown(self) -> None:
        """Request application shutdown programmatically."""
        self._logger.info("Shutdown requested")
        self._shutdown_event.set()


async def run_foreground(settings: "Settings") -> None:
    """
    Run the application in foreground mode.
    
    Args:
        settings: Application settings.
    """
    from ragflow_client.utils.logger import setup_logger
    
    setup_logger(settings, daemon_mode=False)
    
    lifecycle = LifecycleManager(settings)
    await lifecycle.run()
