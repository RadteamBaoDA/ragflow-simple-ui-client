"""
Document Conversion Engine Module.

This module provides platform-specific document-to-PDF converters:
- Windows: Uses Microsoft Office 365 via COM automation
- Linux/macOS: Uses LibreOffice in headless mode

Module Structure:
    engine/
    ├── __init__.py     (this file)
    ├── base.py         (abstract base class and result types)
    ├── factory.py      (platform detection and converter creation)
    ├── linux/          (LibreOffice-based converters)
    │   ├── __init__.py
    │   ├── converter.py (main Linux converter)
    │   ├── word.py     (Word to PDF)
    │   ├── excel.py    (Excel to PDF)
    │   └── powerpoint.py (PowerPoint to PDF)
    └── windows/        (Office COM-based converters)
        ├── __init__.py
        ├── converter.py (main Windows converter)
        ├── word.py     (Word to PDF via COM)
        ├── excel.py    (Excel to PDF via COM)
        └── powerpoint.py (PowerPoint to PDF via COM)

Quick Start:
    from ragflow_client.features.doc_converter.engine import get_converter
    
    # Factory automatically picks the right converter
    converter = get_converter()
    converter.initialize()
    
    result = converter.convert_word(source, target, config)
    
    converter.cleanup()

Author: RAGFlow Team
Created: December 2024
"""

# Import the base class and result type for type hints
from ragflow_client.features.doc_converter.engine.base import (
    BaseConverter,
    ConversionResult,
)

# Import the factory function for creating converters
from ragflow_client.features.doc_converter.engine.factory import (
    get_converter,
    get_converter_info,
)

# Define public API
__all__ = [
    "BaseConverter",     # Abstract base class (for type hints)
    "ConversionResult",  # Result type from conversions
    "get_converter",     # Factory function (use this!)
    "get_converter_info", # Get converter info without creating
]
