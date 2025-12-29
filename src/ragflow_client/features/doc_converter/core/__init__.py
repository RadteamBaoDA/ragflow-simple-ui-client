"""
Core Module for Document Converter.

This module contains core infrastructure components:
- OutputManager: File output organization and summary reports
- PrerequisiteChecker: Office/LibreOffice installation verification

File Structure:
    core/
    ├── __init__.py        (this file)
    ├── output_manager.py  (output file handling and reports)
    └── prerequisite.py    (software installation checks)

Usage:
    from ragflow_client.features.doc_converter.core import (
        OutputManager,
        discover_files,
        check_prerequisites,
        PrerequisiteError,
    )
    
    # Check software requirements
    status = check_prerequisites()
    
    # Setup output manager
    manager = OutputManager(input_dir, output_dir, suffix_config)

Author: RAGFlow Team
"""

from ragflow_client.features.doc_converter.core.output_manager import (
    OutputManager,
    discover_files,
    FileType,
    ConversionError,
    ConversionSummary,
)
from ragflow_client.features.doc_converter.core.prerequisite import (
    check_prerequisites,
    PrerequisiteError,
    PrerequisiteStatus,
)

__all__ = [
    # Output manager
    "OutputManager",
    "discover_files",
    "FileType",
    "ConversionError",
    "ConversionSummary",
    # Prerequisites
    "check_prerequisites",
    "PrerequisiteError",
    "PrerequisiteStatus",
]
