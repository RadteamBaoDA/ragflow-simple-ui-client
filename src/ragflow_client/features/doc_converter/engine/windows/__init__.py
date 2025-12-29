"""
Windows Office 365 COM Engine - Module Initialization.

This module provides a unified interface to all Windows document converters
(Word, Excel, PowerPoint) using Microsoft Office 365 COM automation.

File Structure:
    windows/
    ├── __init__.py     (this file - exports the main converter)
    ├── converter.py    (main converter that delegates to specific converters)
    ├── word.py         (Word document conversion via COM)
    ├── excel.py        (Excel spreadsheet conversion via COM)
    └── powerpoint.py   (PowerPoint presentation conversion via COM)

Usage:
    from ragflow_client.features.doc_converter.engine.windows import WindowsConverter
    
    converter = WindowsConverter()
    converter.initialize()  # Initialize COM - REQUIRED!
    result = converter.convert_word(source, target, config)
    converter.cleanup()     # Clean up COM

Author: RAGFlow Team
Created: December 2024
"""

from ragflow_client.features.doc_converter.engine.windows.converter import WindowsConverter
from ragflow_client.features.doc_converter.engine.windows.word import WindowsWordConverter
from ragflow_client.features.doc_converter.engine.windows.excel import WindowsExcelConverter
from ragflow_client.features.doc_converter.engine.windows.powerpoint import WindowsPowerPointConverter

__all__ = [
    "WindowsConverter",           # Main converter (use this normally)
    "WindowsWordConverter",       # Direct Word converter access
    "WindowsExcelConverter",      # Direct Excel converter access
    "WindowsPowerPointConverter", # Direct PowerPoint converter access
]
