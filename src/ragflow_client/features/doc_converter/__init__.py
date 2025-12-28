"""
Document Converter feature module.

Provides document conversion capabilities (PDF, DOCX, etc.) as an
internal micro-service that subscribes to the event bus.
"""

from ragflow_client.features.doc_converter.worker import DocConverterWorker
from ragflow_client.features.doc_converter.processor import DocumentProcessor
from ragflow_client.features.doc_converter.schema import (
    ConversionJob,
    JobProgress,
    JobResult,
    JobStatus,
)

__all__ = [
    "DocConverterWorker",
    "DocumentProcessor",
    "ConversionJob",
    "JobProgress",
    "JobResult",
    "JobStatus",
]
