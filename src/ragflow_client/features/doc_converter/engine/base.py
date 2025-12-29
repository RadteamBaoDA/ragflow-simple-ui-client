"""
Abstract base class for document converters.

Defines the interface that platform-specific converters must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ragflow_client.features.doc_converter.config import (
        ExcelPrintConfig,
        PowerPointConfig,
        WordConfig,
    )


@dataclass
class ConversionResult:
    """Result of a document conversion."""
    success: bool
    source_path: Path
    output_path: Path | None = None
    error: str | None = None
    duration_seconds: float = 0.0
    pages: int = 0
    metadata: dict[str, str] = field(default_factory=dict)


class BaseConverter(ABC):
    """
    Abstract base class for document converters.
    
    Implementations must provide conversion methods for each document type.
    All conversions run synchronously and should be called via asyncio.to_thread
    for non-blocking operation.
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the converter.
        
        For Windows COM, this should call pythoncom.CoInitialize().
        Must be called from the worker thread.
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up resources.
        
        For Windows COM, this should call pythoncom.CoUninitialize().
        """
        pass
    
    @abstractmethod
    def convert_word(
        self,
        source: Path,
        target: Path,
        config: "WordConfig",
    ) -> ConversionResult:
        """
        Convert a Word document to PDF.
        
        Args:
            source: Path to the Word document (.doc, .docx).
            target: Path for the output PDF.
            config: Word print configuration.
            
        Returns:
            ConversionResult with success status and details.
        """
        pass
    
    @abstractmethod
    def convert_excel(
        self,
        source: Path,
        target: Path,
        config: "ExcelPrintConfig",
        sheet_name: str | None = None,
    ) -> ConversionResult:
        """
        Convert an Excel spreadsheet to PDF.
        
        Args:
            source: Path to the Excel file (.xls, .xlsx, .xlsm).
            target: Path for the output PDF.
            config: Excel print configuration.
            sheet_name: Optional specific sheet to convert.
            
        Returns:
            ConversionResult with success status and details.
        """
        pass
    
    @abstractmethod
    def convert_powerpoint(
        self,
        source: Path,
        target: Path,
        config: "PowerPointConfig",
    ) -> ConversionResult:
        """
        Convert a PowerPoint presentation to PDF.
        
        Args:
            source: Path to the PowerPoint file (.ppt, .pptx).
            target: Path for the output PDF.
            config: PowerPoint print configuration.
            
        Returns:
            ConversionResult with success status and details.
        """
        pass
    
    @abstractmethod
    def convert_xlsm_to_xlsx(
        self,
        source: Path,
        target: Path,
    ) -> ConversionResult:
        """
        Convert XLSM/XLM to XLSX (remove macros).
        
        Args:
            source: Path to the XLSM/XLM file.
            target: Path for the output XLSX.
            
        Returns:
            ConversionResult with success status.
        """
        pass
    
    @property
    @abstractmethod
    def supports_parallel(self) -> bool:
        """
        Whether this converter supports parallel processing.
        
        Some COM applications (like Excel) may have issues with
        multiple concurrent instances.
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the converter."""
        pass
