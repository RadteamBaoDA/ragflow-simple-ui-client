"""
Schema Module for Document Converter Events.

This module defines Pydantic models for event-driven communication:
- Job requests (ConversionJob)
- Progress updates (JobProgress)
- Results (JobResult)
- Job status enum

These models ensure type safety and validation for all event payloads
passed through the event bus.

File Structure:
    schema/
    ├── __init__.py     (this file)
    └── schema.py       (Pydantic models)

Usage:
    from simple_ui_client.features.doc_converter.schema import (
        ConversionJob,
        JobProgress,
        JobResult,
        JobStatus,
    )
    
    job = ConversionJob(source_path=Path("doc.pdf"))
    progress = JobProgress(job_id=job.id, progress=50)

Author: Simple UI Team
"""

from simple_ui_client.features.doc_converter.schema.schema import (
    JobStatus,
    ConversionJob,
    JobProgress,
    JobResult,
)

__all__ = [
    "JobStatus",
    "ConversionJob",
    "JobProgress",
    "JobResult",
]
