import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from ragflow_client.core.bus import Event
from ragflow_client.features.doc_converter.worker.worker import DocConverterWorker
from ragflow_client.features.doc_converter.schema.schema import ConversionJob, JobStatus

@pytest.mark.asyncio
async def test_worker_starts_job(event_bus):
    worker = DocConverterWorker(event_bus)
    
    # Mock DocumentProcessor.process_async
    worker.processor.process_async = AsyncMock()
    
    await worker.start()
    await event_bus.start()
    
    job = ConversionJob(source_path="test.docx")
    await event_bus.publish(Event(
        name="doc:convert",
        payload=job.model_dump(mode="json"),
        source="test"
    ))
    
    # Give it a moment to process
    await asyncio.sleep(0.2)
    
    worker.processor.process_async.assert_called_once()
    assert worker.active_job_count == 0  # Should be done processing (mock is fast)
    
    await worker.stop()
    await event_bus.stop()

@pytest.mark.asyncio
async def test_worker_cancellation(event_bus):
    worker = DocConverterWorker(event_bus)
    
    # Slow processor mock
    async def slow_process(*args):
        await asyncio.sleep(1.0)
    worker.processor.process_async = AsyncMock(side_effect=slow_process)
    
    await worker.start()
    await event_bus.start()
    
    job = ConversionJob(source_path="test.docx")
    await event_bus.publish(Event(
        name="doc:convert",
        payload=job.model_dump(mode="json"),
        source="test"
    ))
    
    await asyncio.sleep(0.1)
    assert worker.active_job_count == 1
    
    # Send cancel
    await event_bus.publish(Event(
        name="doc:cancel",
        payload={"id": str(job.id)},
        source="test"
    ))
    
    await asyncio.sleep(0.2)
    assert worker.active_job_count == 0
    
    await worker.stop()
    await event_bus.stop()
