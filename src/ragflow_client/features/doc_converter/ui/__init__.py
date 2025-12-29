"""
UI Module for Document Converter.

This module contains user interface components for the CLI:
- ProgressManager: Rich-based progress display with ETA

File Structure:
    ui/
    ├── __init__.py      (this file)
    └── progress_ui.py   (Rich progress display)

Usage:
    from ragflow_client.features.doc_converter.ui import ProgressManager
    
    with ProgressManager(total_files=10) as pm:
        pm.start_file("document.docx")
        pm.update_file("document.docx", "converting", 50)
        pm.complete_file("document.docx")

Author: RAGFlow Team
"""

from ragflow_client.features.doc_converter.ui.progress_ui import (
    ProgressManager,
    FileStatus,
    LogEntry,
)

__all__ = [
    "ProgressManager",
    "FileStatus",
    "LogEntry",
]
