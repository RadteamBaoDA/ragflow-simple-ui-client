"""
Linux LibreOffice Engine - Main Converter.

This is the main entry point for Linux document conversion. It implements
the BaseConverter interface and delegates to specific converters for
each document type (Word, Excel, PowerPoint).

This design pattern allows:
1. Easy testing of individual converters
2. Consistent interface across platforms
3. Simple addition of new document types

Author: Simple UI Team
Created: December 2024
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

# Import the abstract base class that defines our interface
from simple_ui_client.features.doc_converter.engine.base import (
    BaseConverter,
    ConversionResult,
)

# Import individual document converters
from simple_ui_client.features.doc_converter.engine.linux.word import LinuxWordConverter
from simple_ui_client.features.doc_converter.engine.linux.excel import LinuxExcelConverter
from simple_ui_client.features.doc_converter.engine.linux.powerpoint import LinuxPowerPointConverter

if TYPE_CHECKING:
    from simple_ui_client.features.doc_converter.config import (
        ExcelPrintConfig,
        PowerPointConfig,
        WordConfig,
    )


class LinuxConverter(BaseConverter):
    """
    Main Linux converter implementing the BaseConverter interface.
    
    This class:
    1. Creates instances of specific document converters
    2. Delegates conversion calls to the appropriate converter
    3. Provides a unified interface for all document types
    
    Benefits of this design:
    - Each document type can be maintained separately
    - Easy to add new document types
    - Consistent error handling across types
    - Simple testing and debugging
    
    Threading: LibreOffice supports parallel execution with multiple
    instances. Each instance gets a separate process, avoiding conflicts.
    
    Example:
        converter = LinuxConverter()
        converter.initialize()  # Optional on Linux
        
        # Convert a Word document
        result = converter.convert_word(source, target, config)
        
        converter.cleanup()  # Optional on Linux
    """
    
    def __init__(self, libreoffice_path: str = "libreoffice") -> None:
        """
        Initialize the Linux converter with all document type converters.
        
        Args:
            libreoffice_path: Path to the LibreOffice executable.
                            Default is "libreoffice" which works if LibreOffice
                            is installed and in the system PATH.
                            
                            On some systems, you might need:
                            - "/usr/bin/libreoffice"
                            - "/snap/bin/libreoffice"
                            - "/opt/libreoffice/program/soffice"
        """
        # Store path for reference
        self._libreoffice_path = libreoffice_path
        
        # Create individual converters for each document type
        # Each converter handles one document type independently
        self._word_converter = LinuxWordConverter(libreoffice_path)
        self._excel_converter = LinuxExcelConverter(libreoffice_path)
        self._powerpoint_converter = LinuxPowerPointConverter(libreoffice_path)
        
        # Setup logging with component context
        self._logger = logger.bind(component="LinuxConverter")
        
        self._logger.debug(f"Initialized with LibreOffice path: {libreoffice_path}")
    
    def initialize(self) -> None:
        """
        Initialize the converter.
        
        On Linux with LibreOffice, no special initialization is needed.
        Each subprocess handles its own LibreOffice instance.
        
        This method exists to satisfy the BaseConverter interface.
        On Windows, this is where COM would be initialized.
        """
        # No-op for LibreOffice - each subprocess is independent
        self._logger.debug("Linux converter ready (no initialization needed)")
    
    def cleanup(self) -> None:
        """
        Clean up resources.
        
        On Linux with LibreOffice, no cleanup is needed.
        Subprocesses clean themselves up when they exit.
        
        This method exists to satisfy the BaseConverter interface.
        On Windows, this would uninitialize COM.
        """
        # No-op for LibreOffice - subprocesses handle their own cleanup
        self._logger.debug("Linux converter cleanup (no action needed)")
    
    def convert_word(
        self,
        source: Path,
        target: Path,
        config: "WordConfig",
    ) -> ConversionResult:
        """
        Convert a Word document to PDF.
        
        Delegates to LinuxWordConverter for the actual conversion.
        
        Args:
            source: Path to the Word document (.doc, .docx, .rtf, .odt).
            target: Desired output path for the PDF file.
            config: Word print configuration.
        
        Returns:
            ConversionResult with success status and details.
        """
        return self._word_converter.convert(source, target, config)
    
    def convert_excel(
        self,
        source: Path,
        target: Path,
        config: "ExcelPrintConfig",
        sheet_name: str | None = None,
    ) -> ConversionResult:
        """
        Convert an Excel spreadsheet to PDF.
        
        Delegates to LinuxExcelConverter for the actual conversion.
        
        Args:
            source: Path to the Excel file (.xls, .xlsx, .xlsm, .ods).
            target: Desired output path for the PDF file.
            config: Excel print configuration.
            sheet_name: Optional specific sheet to convert (limited support).
        
        Returns:
            ConversionResult with success status and details.
        """
        return self._excel_converter.convert(source, target, config, sheet_name)
    
    def convert_powerpoint(
        self,
        source: Path,
        target: Path,
        config: "PowerPointConfig",
    ) -> ConversionResult:
        """
        Convert a PowerPoint presentation to PDF.
        
        Delegates to LinuxPowerPointConverter for the actual conversion.
        
        Args:
            source: Path to the PowerPoint file (.ppt, .pptx, .odp).
            target: Desired output path for the PDF file.
            config: PowerPoint print configuration.
        
        Returns:
            ConversionResult with success status and details.
        """
        return self._powerpoint_converter.convert(source, target, config)
    
    def convert_xlsm_to_xlsx(
        self,
        source: Path,
        target: Path,
    ) -> ConversionResult:
        """
        Convert a macro-enabled Excel file to standard XLSX.
        
        Removes VBA macros while preserving data and formatting.
        Delegates to LinuxExcelConverter.
        
        Args:
            source: Path to the XLSM/XLSB file with macros.
            target: Path for the output XLSX file (without macros).
        
        Returns:
            ConversionResult with success status and details.
        """
        return self._excel_converter.convert_xlsm_to_xlsx(source, target)
    
    @property
    def supports_parallel(self) -> bool:
        """
        Whether this converter supports parallel processing.
        
        LibreOffice supports running multiple instances simultaneously.
        Each conversion runs in a separate subprocess, so there are
        no conflicts between parallel conversions.
        
        Returns:
            True - LibreOffice supports parallel execution.
        """
        return True
    
    @property
    def name(self) -> str:
        """
        Human-readable name of this converter.
        
        Used for logging and user messages.
        
        Returns:
            String identifying this converter.
        """
        return "Linux LibreOffice"
