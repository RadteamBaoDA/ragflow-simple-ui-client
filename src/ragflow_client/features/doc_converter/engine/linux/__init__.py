"""
Linux LibreOffice Engine - Module Initialization.

This module provides a unified interface to all Linux document converters
(Word, Excel, PowerPoint) using LibreOffice in headless mode.

File Structure:
    linux/
    ├── __init__.py     (this file - exports the main converter)
    ├── converter.py    (main converter that delegates to specific converters)
    ├── word.py         (Word document conversion)
    ├── excel.py        (Excel spreadsheet conversion)
    └── powerpoint.py   (PowerPoint presentation conversion)

Usage:
    from ragflow_client.features.doc_converter.engine.linux import LinuxConverter
    
    converter = LinuxConverter()
    result = converter.convert_word(source, target, config)

Author: RAGFlow Team
Created: December 2024
"""

# Import the main converter class that provides all conversion methods
from ragflow_client.features.doc_converter.engine.linux.converter import LinuxConverter

# Import individual converters for direct access if needed
from ragflow_client.features.doc_converter.engine.linux.word import LinuxWordConverter
from ragflow_client.features.doc_converter.engine.linux.excel import LinuxExcelConverter
from ragflow_client.features.doc_converter.engine.linux.powerpoint import LinuxPowerPointConverter

# Define what gets exported when using "from linux import *"
__all__ = [
    "LinuxConverter",          # Main converter (use this normally)
    "LinuxWordConverter",      # Direct Word converter access
    "LinuxExcelConverter",     # Direct Excel converter access
    "LinuxPowerPointConverter", # Direct PowerPoint converter access
]
