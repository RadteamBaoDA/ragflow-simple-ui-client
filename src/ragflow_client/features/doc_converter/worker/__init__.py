"""
Worker Module for Document Converter.

This module contains the event bus workers and processing logic:
- DocConverterWorker: Event bus subscriber for doc:convert events
- BatchWorker: CLI batch processing with parallel execution
- DocumentProcessor: Core document processing logic

File Structure:
    worker/
    ├── __init__.py      (this file)
    ├── worker.py        (event bus worker - subscribes to events)
    ├── batch_worker.py  (CLI batch processing with thread pool)
    └── processor.py     (document processing logic)

Event-Driven Flow:
    1. SocketService receives doc:convert event
    2. DocConverterWorker subscribes and receives event
    3. Worker creates task, calls DocumentProcessor
    4. Progress published via doc:progress event
    5. Result published via doc:result event

Usage:
    # For event bus integration
    from ragflow_client.features.doc_converter.worker import DocConverterWorker
    worker = DocConverterWorker(event_bus)
    await worker.start()
    
    # For CLI batch processing
    from ragflow_client.features.doc_converter.worker import BatchWorker
    batch = BatchWorker(config, progress_manager)
    await batch.process_batch(files, output_manager)

Author: RAGFlow Team
"""

from ragflow_client.features.doc_converter.worker.worker import DocConverterWorker
from ragflow_client.features.doc_converter.worker.batch_worker import BatchWorker
from ragflow_client.features.doc_converter.worker.processor import DocumentProcessor

__all__ = [
    "DocConverterWorker",  # Event bus worker
    "BatchWorker",         # CLI batch processor
    "DocumentProcessor",   # Core processing logic
]
