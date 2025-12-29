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
    from simple_ui_client.features.doc_converter.engine.linux import LinuxConverter
    
    converter = LinuxConverter()
    result = converter.convert_word(source, target, config)

Author: Simple UI Team
Created: December 2024
"""

# Import the main converter class that provides all conversion methods
from simple_ui_client.features.doc_converter.engine.linux.converter import LinuxConverter

# Import individual converters for direct access if needed
from simple_ui_client.features.doc_converter.engine.linux.word import LinuxWordConverter
from simple_ui_client.features.doc_converter.engine.linux.excel import LinuxExcelConverter
from simple_ui_client.features.doc_converter.engine.linux.powerpoint import LinuxPowerPointConverter

# Define what gets exported when using "from linux import *"
__all__ = [
    "LinuxConverter",          # Main converter (use this normally)
    "LinuxWordConverter",      # Direct Word converter access
    "LinuxExcelConverter",     # Direct Excel converter access
    "LinuxPowerPointConverter", # Direct PowerPoint converter access
]
