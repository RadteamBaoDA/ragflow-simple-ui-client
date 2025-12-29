import pytest
import asyncio
from pathlib import Path
from ragflow_client.core.bus import EventBus
from ragflow_client.utils.config import Settings

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
        ragflow_home=temp_dir / ".ragflow",
        websocket_url="http://localhost:5000",
        websocket_api_key="test_key"
    )
