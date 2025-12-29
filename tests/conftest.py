import pytest
import asyncio
from pathlib import Path
from simple_ui_client.core.bus import EventBus
from simple_ui_client.utils.config import Settings

@pytest.fixture
def event_bus():
    """Shared event bus fixture."""
    return EventBus()

@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory fixture."""
    return tmp_path

@pytest.fixture
def settings(temp_dir):
    """Basic settings fixture."""
    return Settings(
        simple_ui_home=temp_dir / ".simple-ui",
        websocket_url="http://localhost:5000",
        websocket_api_key="test_key"
    )
