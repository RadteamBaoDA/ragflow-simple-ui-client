"""
Core modules for Simple UI client.

Provides the internal event bus, daemon management, and lifecycle handling.
"""

from simple_ui_client.core.bus import EventBus, Event, get_event_bus
from simple_ui_client.core.lifecycle import LifecycleManager

__all__ = ["EventBus", "Event", "get_event_bus", "LifecycleManager"]
