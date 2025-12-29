"""
Document converter worker.

Subscribes to the event bus for conversion requests and coordinates
the document processor. Publishes progress and results back to the bus.
"""

import asyncio
from typing import TYPE_CHECKING, Any

from loguru import logger

from ragflow_client.core.bus import Event, EventPayload
from ragflow_client.features.doc_converter.worker.processor import DocumentProcessor
from ragflow_client.features.doc_converter.schema.schema import (
    ConversionJob,
    JobProgress,
    JobResult,
    JobStatus,
)

if TYPE_CHECKING:
    from ragflow_client.core.bus import EventBus


class DocConverterWorker:
    """
    Event bus worker for document conversion.
    
    Subscribes to `doc:convert` events, processes documents using
    DocumentProcessor, and publishes progress/results back to the bus.
    
    Example:
        worker = DocConverterWorker(event_bus)
        await worker.start()
    """
    
    def __init__(self, bus: "EventBus") -> None:
        """
        Initialize the worker.
        
        Args:
            bus: The event bus to subscribe to.
        """
        self.bus = bus
        self.processor = DocumentProcessor()
        self._active_jobs: dict[str, asyncio.Task[None]] = {}
        self._logger = logger.bind(component="DocConverterWorker")
    
    async def start(self) -> None:
        """Start the worker and subscribe to events."""
        self.bus.subscribe("doc:convert", self._on_convert_request)
        self.bus.subscribe("doc:cancel", self._on_cancel_request)
        self._logger.info("Document converter worker started")
    
    async def stop(self) -> None:
        """Stop the worker and cancel active jobs."""
        # Cancel all active jobs
        for job_id, task in self._active_jobs.items():
            if not task.done():
                task.cancel()
                self._logger.warning(f"Cancelled job {job_id}")
        
        self._active_jobs.clear()
        
        # Unsubscribe from events
        self.bus.unsubscribe("doc:convert", self._on_convert_request)
        self.bus.unsubscribe("doc:cancel", self._on_cancel_request)
        
        self._logger.info("Document converter worker stopped")
    
    async def _on_convert_request(self, event: Event) -> None:
        """
        Handle a document conversion request.
        
        Args:
            event: The conversion request event.
        """
        try:
            # Parse job from event payload
            payload = event.payload
            if isinstance(payload, dict):
                job = ConversionJob(**payload)
            elif isinstance(payload, ConversionJob):
                job = payload
            else:
                self._logger.error(f"Invalid payload type: {type(payload)}")
                return
            
            job_id = str(job.id)
            
            # Check if job is already running
            if job_id in self._active_jobs:
                self._logger.warning(f"Job {job_id} already running")
                return
            
            self._logger.info(f"Starting conversion job: {job_id}")
            
            # Create task for processing
            task = asyncio.create_task(self._process_job(job))
            self._active_jobs[job_id] = task
            
            # Clean up when done
            task.add_done_callback(lambda t: self._active_jobs.pop(job_id, None))
            
        except Exception as e:
            self._logger.exception(f"Error handling convert request: {e}")
    
    async def _on_cancel_request(self, event: Event) -> None:
        """
        Handle a job cancellation request.
        
        Args:
            event: The cancellation request event.
        """
        payload = event.payload
        job_id = payload.get("id") if isinstance(payload, dict) else None
        
        if not job_id:
            self._logger.warning("Cancel request missing job ID")
            return
        
        job_id = str(job_id)
        task = self._active_jobs.get(job_id)
        
        if task and not task.done():
            task.cancel()
            self._logger.info(f"Cancelled job: {job_id}")
            
            # Publish cancellation event
            await self.bus.publish(Event(
                name="doc:cancelled",
                payload={"id": job_id},
                source="DocConverterWorker",
            ))
        else:
            self._logger.warning(f"Job not found or already done: {job_id}")
    
    async def _process_job(self, job: ConversionJob) -> None:
        """
        Process a conversion job and publish results.
        
        Args:
            job: The job to process.
        """
        job_id = str(job.id)
        
        try:
            # Publish progress callback
            async def on_progress(progress: int, message: str) -> None:
                await self.bus.publish(Event(
                    name="doc:progress",
                    payload=JobProgress(
                        job_id=job.id,
                        progress=progress,
                        message=message,
                    ).model_dump(mode="json"),
                    source="DocConverterWorker",
                ))
            
            # Wrapper for sync callback
            def progress_sync(progress: int, message: str) -> None:
                # Schedule async callback
                asyncio.get_event_loop().call_soon_threadsafe(
                    lambda: asyncio.create_task(on_progress(progress, message))
                )
            
            # Process the document
            result = await self.processor.process_async(job, progress_sync)
            
            # Publish result
            await self.bus.publish(Event(
                name="doc:result",
                payload=result.model_dump(mode="json"),
                source="DocConverterWorker",
            ))
            
            self._logger.info(
                f"Job {job_id} completed | success={result.success} | "
                f"duration={result.duration_ms}ms"
            )
            
        except asyncio.CancelledError:
            self._logger.info(f"Job {job_id} was cancelled")
            
            # Publish cancellation result
            await self.bus.publish(Event(
                name="doc:result",
                payload=JobResult(
                    job_id=job.id,
                    success=False,
                    error="Job cancelled",
                ).model_dump(mode="json"),
                source="DocConverterWorker",
            ))
            
        except Exception as e:
            self._logger.exception(f"Job {job_id} failed: {e}")
            
            # Publish error result
            await self.bus.publish(Event(
                name="doc:result",
                payload=JobResult(
                    job_id=job.id,
                    success=False,
                    error=str(e),
                ).model_dump(mode="json"),
                source="DocConverterWorker",
            ))
    
    @property
    def active_job_count(self) -> int:
        """Get the number of active jobs."""
        return len(self._active_jobs)
