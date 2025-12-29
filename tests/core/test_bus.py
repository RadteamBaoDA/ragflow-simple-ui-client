import asyncio
import pytest
from ragflow_client.core.bus import Event, EventBus

@pytest.mark.asyncio
async def test_bus_publish_subscribe(event_bus):
    """Test basic publish/subscribe functionality."""
    received = []
    
    async def handler(event: Event):
        received.append(event)
        
    event_bus.subscribe("test:event", handler)
    await event_bus.start()
    
    event = Event(name="test:event", payload={"data": 123})
    await event_bus.publish(event)
    
    # Wait for dispatch
    await asyncio.sleep(0.1)
    
    assert len(received) == 1
    assert received[0].name == "test:event"
    assert received[0].payload == {"data": 123}
    
    await event_bus.stop()

@pytest.mark.asyncio
async def test_bus_wildcard_subscription(event_bus):
    """Test wildcard subscriptions (e.g., doc:*)."""
    received = []
    
    async def handler(event: Event):
        received.append(event)
        
    event_bus.subscribe("doc:*", handler)
    await event_bus.start()
    
    await event_bus.publish(Event(name="doc:convert"))
    await event_bus.publish(Event(name="doc:progress"))
    await event_bus.publish(Event(name="other:event"))
    
    await asyncio.sleep(0.1)
    
    assert len(received) == 2
    assert all(e.name.startswith("doc:") for e in received)
    
    await event_bus.stop()

@pytest.mark.asyncio
async def test_bus_unsubscribe(event_bus):
    """Test unsubscribing a handler."""
    calls = 0
    
    async def handler(event: Event):
        nonlocal calls
        calls += 1
        
    event_bus.subscribe("test:event", handler)
    await event_bus.start()
    
    await event_bus.publish(Event(name="test:event"))
    await asyncio.sleep(0.1)
    assert calls == 1
    
    event_bus.unsubscribe("test:event", handler)
    await event_bus.publish(Event(name="test:event"))
    await asyncio.sleep(0.1)
    assert calls == 1
    
    await event_bus.stop()

@pytest.mark.asyncio
async def test_bus_history(event_bus):
    """Test event history tracking."""
    event_bus._max_history = 5
    await event_bus.start()
    
    for i in range(10):
        await event_bus.publish(Event(name=f"event:{i}"))
        
    await asyncio.sleep(0.1)
    
    history = event_bus.history
    assert len(history) == 5
    assert history[-1].name == "event:9"
    
    await event_bus.stop()
