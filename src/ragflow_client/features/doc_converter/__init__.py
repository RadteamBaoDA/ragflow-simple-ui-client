"""
Document Converter Feature Module.

Event-driven microservice for document conversion (Word, Excel, PowerPoint to PDF).
Subscribes to the event bus for conversion requests and publishes progress/results.

Module Structure (Event-Driven Pattern):
    doc_converter/
    ├── __init__.py          (this file)
    ├── config/              (configuration system)
    │   ├── __init__.py
    │   └── converter_config.py
    ├── core/                (infrastructure components)
    │   ├── __init__.py
    │   ├── output_manager.py
    │   └── prerequisite.py
    ├── engine/              (platform-specific converters)
    │   ├── linux/
    │   └── windows/
    ├── schema/              (event payload models)
    │   ├── __init__.py
    │   └── schema.py
    ├── ui/                  (CLI UI components)
    │   ├── __init__.py
    │   └── progress_ui.py
    └── worker/              (event bus workers)
        ├── __init__.py
        ├── worker.py
        ├── batch_worker.py
        └── processor.py

Event Flow:
    1. doc:convert -> DocConverterWorker receives job
    2. doc:progress -> Progress updates published
    3. doc:result -> Final result published

Usage:
    # Event bus integration
    from ragflow_client.features.doc_converter import DocConverterWorker
    worker = DocConverterWorker(event_bus)
    await worker.start()
    
    # CLI batch processing
    from ragflow_client.features.doc_converter import BatchWorker, ConverterConfig
    config = ConverterConfig.load(Path("config.yaml"))
    worker = BatchWorker(config, progress_manager)

Author: RAGFlow Team
"""

# Configuration
from ragflow_client.features.doc_converter.config import ConverterConfig

# Core infrastructure
from ragflow_client.features.doc_converter.core import (
    OutputManager,
    discover_files,
    FileType,
    check_prerequisites,
    PrerequisiteError,
)

# Event schema
from ragflow_client.features.doc_converter.schema import (
    ConversionJob,
    JobProgress,
    JobResult,
    JobStatus,
)

# UI components
from ragflow_client.features.doc_converter.ui import ProgressManager

# Workers
from ragflow_client.features.doc_converter.worker import (
    DocConverterWorker,
    BatchWorker,
    DocumentProcessor,
)

__all__ = [
    # Config
    "ConverterConfig",
    # Core
    "OutputManager",
    "discover_files",
    "FileType",
    "check_prerequisites",
    "PrerequisiteError",
    # Schema
    "ConversionJob",
    "JobProgress",
    "JobResult",
    "JobStatus",
    # UI
    "ProgressManager",
    # Workers
    "DocConverterWorker",
    "BatchWorker",
    "DocumentProcessor",
]
