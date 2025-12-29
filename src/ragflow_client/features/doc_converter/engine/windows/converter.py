"""
Windows Office 365 COM Engine - Main Converter.

This is the main entry point for Windows document conversion. It implements
the BaseConverter interface and delegates to specific converters for
each document type (Word, Excel, PowerPoint).

This design allows:
- Individual converters can be tested/debugged independently
- Easy to add new document types
- Consistent interface matching the Linux converter

Author: RAGFlow Team  
Created: December 2024
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from ragflow_client.features.doc_converter.engine.base import (
    BaseConverter,
    ConversionResult,
)
from ragflow_client.features.doc_converter.engine.windows.word import WindowsWordConverter
from ragflow_client.features.doc_converter.engine.windows.excel import WindowsExcelConverter
from ragflow_client.features.doc_converter.engine.windows.powerpoint import WindowsPowerPointConverter

if TYPE_CHECKING:
    from ragflow_client.features.doc_converter.config import (
        ExcelPrintConfig,
        PowerPointConfig,
        WordConfig,
    )


class WindowsConverter(BaseConverter):
    """
    Main Windows converter implementing BaseConverter interface.
    
    Uses Microsoft Office 365 through COM automation for high-fidelity
    document to PDF conversion. Each document type has a dedicated
    converter for maintainability.
    
    Threading:
        - COM must be initialized per-thread (call initialize())
        - Each thread should have its own converter instance
        - Office applications run as separate processes
    
    Parallel support:
        - Word: Generally works well in parallel
        - Excel: Can have issues with complex workbooks
        - PowerPoint: Works well in parallel
        
        If parallel fails, the batch worker falls back to sequential.
    
    Example:
        converter = WindowsConverter()
        converter.initialize()  # Required!
        try:
            result = converter.convert_word(source, target, config)
        finally:
            converter.cleanup()  # Always cleanup!
    """
    
    def __init__(self) -> None:
        """
        Initialize the Windows converter.
        
        Creates instances of all document-type converters.
        COM initialization happens in initialize(), not here.
        """
        self._word_converter = WindowsWordConverter()
        self._excel_converter = WindowsExcelConverter()
        self._powerpoint_converter = WindowsPowerPointConverter()
        self._logger = logger.bind(component="WindowsConverter")
        self._initialized = False
    
    def initialize(self) -> None:
        """
        Initialize COM for all converters in the current thread.
        
        MUST be called before any conversion operations.
        Call from the same thread that will do conversions.
        """
        if self._initialized:
            return
        
        self._word_converter.initialize()
        self._excel_converter.initialize()
        self._powerpoint_converter.initialize()
        self._initialized = True
        self._logger.debug("Windows converter initialized")
    
    def cleanup(self) -> None:
        """
        Clean up COM resources for all converters.
        
        MUST be called when done with conversions.
        Call from the same thread that called initialize().
        """
        if not self._initialized:
            return
        
        self._word_converter.cleanup()
        self._excel_converter.cleanup()
        self._powerpoint_converter.cleanup()
        self._initialized = False
        self._logger.debug("Windows converter cleanup complete")
    
    def convert_word(
        self,
        source: Path,
        target: Path,
        config: "WordConfig",
    ) -> ConversionResult:
        """Convert Word document to PDF via WindowsWordConverter."""
        return self._word_converter.convert(source, target, config)
    
    def convert_excel(
        self,
        source: Path,
        target: Path,
        config: "ExcelPrintConfig",
        sheet_name: str | None = None,
    ) -> ConversionResult:
        """Convert Excel spreadsheet to PDF via WindowsExcelConverter."""
        return self._excel_converter.convert(source, target, config, sheet_name)
    
    def convert_powerpoint(
        self,
        source: Path,
        target: Path,
        config: "PowerPointConfig",
    ) -> ConversionResult:
        """Convert PowerPoint presentation to PDF via WindowsPowerPointConverter."""
        return self._powerpoint_converter.convert(source, target, config)
    
    def convert_xlsm_to_xlsx(
        self,
        source: Path,
        target: Path,
    ) -> ConversionResult:
        """Convert macro Excel to XLSX via WindowsExcelConverter."""
        return self._excel_converter.convert_xlsm_to_xlsx(source, target)
    
    @property
    def supports_parallel(self) -> bool:
        """
        Whether parallel processing is supported.
        
        Windows COM generally supports parallel, but some workbooks
        may cause issues. The batch worker will fallback to sequential
        if too many parallel failures occur.
        """
        return True
    
    @property
    def name(self) -> str:
        """Human-readable converter name."""
        return "Windows Office 365 COM"
