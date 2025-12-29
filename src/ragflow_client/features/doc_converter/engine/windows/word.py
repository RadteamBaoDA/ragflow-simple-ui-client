"""
Windows Office 365 COM Engine - Word Converter Module.

This module handles conversion of Word documents (.doc, .docx, .rtf)
to PDF format using Microsoft Word through COM automation on Windows.

COM (Component Object Model) allows Python to control Word as if a user
were operating it, providing full access to Word's features including
all print and export options.

Requirements:
    - Microsoft Office 365 or Office 2016+ installed
    - pywin32 package (pip install pywin32)

Threading:
    COM must be initialized per-thread. Call pythoncom.CoInitialize()
    before using COM objects and CoUninitialize() when done.

Author: RAGFlow Team
Created: December 2024
"""

from __future__ import annotations

import time  # Measure conversion duration
from pathlib import Path  # Cross-platform path handling
from typing import TYPE_CHECKING  # Type hints without runtime import

from loguru import logger  # Structured logging

from ragflow_client.features.doc_converter.engine.base import ConversionResult

if TYPE_CHECKING:
    from ragflow_client.features.doc_converter.converter_config import (
        MarginType,
        WordConfig,
    )


# ============================================================================
# Word PDF Export Constants
# ============================================================================
# These constants match Microsoft Word's internal values.
# Reference: https://docs.microsoft.com/en-us/office/vba/api/word.wdexportformat

# Export format for PDF (Word internal constant)
WD_EXPORT_FORMAT_PDF = 17

# Optimization setting for PDF export (printing vs screen)
WD_EXPORT_OPTIMIZE_FOR_PRINT = 0
WD_EXPORT_OPTIMIZE_FOR_ON_SCREEN = 1

# Page orientation constants
WD_ORIENT_PORTRAIT = 0
WD_ORIENT_LANDSCAPE = 1


class WindowsWordConverter:
    """
    Converts Word documents to PDF using Microsoft Word COM automation.
    
    This converter provides full access to Word's PDF export features:
    - Custom margins (top, bottom, left, right)
    - Page orientation (portrait/landscape)
    - Paper size selection
    - Font embedding
    - High-quality PDF output
    
    Supported formats:
        - .doc   (Legacy Word 97-2003 format)
        - .docx  (Modern Word format, Office 2007+)
        - .rtf   (Rich Text Format)
    
    Threading notes:
        - Each thread must call initialize() before use
        - Always call cleanup() when done
        - Don't share Word instances between threads
    
    Example:
        converter = WindowsWordConverter()
        converter.initialize()  # Required for COM
        try:
            result = converter.convert(source, target, config)
        finally:
            converter.cleanup()
    """
    
    def __init__(self) -> None:
        """
        Initialize the Word converter.
        
        Note: This only sets up the converter object.
        COM initialization happens in initialize() method,
        which must be called from the worker thread.
        """
        # Track whether COM has been initialized in current thread
        self._initialized = False
        
        # Logger with component context for filtering
        self._logger = logger.bind(component="WindowsWordConverter")
    
    def initialize(self) -> None:
        """
        Initialize COM for the current thread.
        
        CRITICAL: Must be called from the same thread that will use COM.
        
        COM (Component Object Model) is Windows' technology for inter-process
        communication. Python threads must initialize COM before using it.
        
        How it works:
        1. CoInitialize() sets up COM for single-threaded apartment
        2. This allows creating COM objects like Word.Application
        3. Must be paired with CoUninitialize() when done
        
        Raises:
            RuntimeError: If COM initialization fails.
        """
        if self._initialized:
            # Already initialized in this thread - skip
            return
        
        try:
            # Import Windows-specific modules
            # These only work on Windows - import error on Linux/Mac
            import pythoncom
            
            # Initialize COM for this thread
            # CoInitialize sets up single-threaded apartment (STA) model
            pythoncom.CoInitialize()
            
            self._initialized = True
            self._logger.debug("COM initialized for Word converter")
            
        except ImportError:
            self._logger.error("pywin32 not installed - pip install pywin32")
            raise RuntimeError("pywin32 package required for Windows converter")
        except Exception as e:
            self._logger.error(f"COM initialization failed: {e}")
            raise RuntimeError(f"COM initialization failed: {e}")
    
    def cleanup(self) -> None:
        """
        Clean up COM resources.
        
        CRITICAL: Must be called from the same thread that called initialize().
        
        This releases COM resources and unregisters the thread from COM.
        Failing to call this can cause resource leaks and issues with
        subsequent COM operations.
        """
        if not self._initialized:
            return
        
        try:
            import pythoncom
            
            # Uninitialize COM for this thread
            # Releases all COM resources acquired in this thread
            pythoncom.CoUninitialize()
            
            self._initialized = False
            self._logger.debug("COM uninitialized for Word converter")
            
        except Exception as e:
            self._logger.warning(f"Error during COM cleanup: {e}")
    
    def _get_margin_inches(self, margin_type: "MarginType") -> tuple[float, float, float, float]:
        """
        Get margin values in inches for a margin preset.
        
        Word uses inches for margins in the English version.
        These values match Word's built-in margin presets.
        
        Args:
            margin_type: One of 'normal', 'narrow', 'wide', 'custom'.
        
        Returns:
            Tuple of (top, bottom, left, right) margins in inches.
        """
        from ragflow_client.features.doc_converter.converter_config import MarginType
        
        # Map margin presets to values (in inches)
        # These match Word's File > Page Setup > Margins presets
        presets = {
            MarginType.NORMAL: (1.0, 1.0, 1.25, 1.25),  # Word default
            MarginType.NARROW: (0.5, 0.5, 0.5, 0.5),    # Minimal margins
            MarginType.WIDE: (1.0, 1.0, 2.0, 2.0),      # Extra side margins
        }
        
        return presets.get(margin_type, presets[MarginType.NORMAL])
    
    def convert(
        self,
        source: Path,
        target: Path,
        config: "WordConfig",
    ) -> ConversionResult:
        """
        Convert a Word document to PDF using COM automation.
        
        This method:
        1. Opens the document in Word (invisible mode)
        2. Applies page setup settings from config
        3. Exports to PDF using Word's built-in exporter
        4. Closes Word and returns result
        
        Args:
            source: Path to the Word document (.doc, .docx, .rtf).
                   Must be an existing file.
            target: Path for the output PDF file.
                   Parent directory will be created if needed.
            config: Word configuration containing:
                   - orientation: 'portrait' or 'landscape'
                   - margins: 'normal', 'narrow', 'wide', or 'custom'
                   - margins_custom: Custom margin values if margins='custom'
                   - paper_size: Paper size like 'A4', 'Letter'
        
        Returns:
            ConversionResult containing:
                - success: True if conversion completed
                - output_path: Path to created PDF
                - error: Error message if failed
                - duration_seconds: Time taken
                - pages: Number of pages in document
        
        Notes:
            - Word is opened invisibly (no window shown)
            - All alerts/dialogs are suppressed
            - Original document is not modified
        """
        start_time = time.time()
        
        # References to COM objects - need for cleanup
        word = None
        doc = None
        
        try:
            # Import Windows COM library
            import win32com.client
            from ragflow_client.features.doc_converter.converter_config import (
                MarginType,
                Orientation,
            )
            
            self._logger.info(f"Converting Word document: {source.name}")
            
            # ===================================================================
            # STEP 1: Create Word Application Instance
            # ===================================================================
            # Dispatch creates a COM connection to Word
            # "Word.Application" is the ProgID for Microsoft Word
            word = win32com.client.Dispatch("Word.Application")
            
            # Make Word invisible - no window shown to user
            word.Visible = False
            
            # Suppress all alerts and confirmation dialogs
            # This prevents Word from prompting during conversion
            word.DisplayAlerts = False
            
            # ===================================================================
            # STEP 2: Open the Document
            # ===================================================================
            # Open document at specified path
            # Must use absolute path as string for COM
            doc = word.Documents.Open(str(source.absolute()))
            
            # ===================================================================
            # STEP 3: Apply Page Setup from Configuration
            # ===================================================================
            # Get the page setup object for the document
            page_setup = doc.PageSetup
            
            # Set page orientation
            if config.orientation == Orientation.LANDSCAPE:
                page_setup.Orientation = WD_ORIENT_LANDSCAPE
            else:
                page_setup.Orientation = WD_ORIENT_PORTRAIT
            
            # Set margins based on configuration
            if config.margins == MarginType.CUSTOM:
                # Use custom margin values from config
                # InchesToPoints converts inches to Word's internal units (points)
                # 1 inch = 72 points
                page_setup.TopMargin = word.InchesToPoints(config.margins_custom.top)
                page_setup.BottomMargin = word.InchesToPoints(config.margins_custom.bottom)
                page_setup.LeftMargin = word.InchesToPoints(config.margins_custom.left)
                page_setup.RightMargin = word.InchesToPoints(config.margins_custom.right)
            else:
                # Use preset margin values
                top, bottom, left, right = self._get_margin_inches(config.margins)
                page_setup.TopMargin = word.InchesToPoints(top)
                page_setup.BottomMargin = word.InchesToPoints(bottom)
                page_setup.LeftMargin = word.InchesToPoints(left)
                page_setup.RightMargin = word.InchesToPoints(right)
            
            # ===================================================================
            # STEP 4: Create Output Directory
            # ===================================================================
            target.parent.mkdir(parents=True, exist_ok=True)
            
            # ===================================================================
            # STEP 5: Export Document to PDF
            # ===================================================================
            # ExportAsFixedFormat is Word's PDF export method
            # Arguments:
            #   OutputFileName: Full path for output file
            #   ExportFormat: PDF format constant (17)
            #   OpenAfterExport: Don't open PDF after creating
            #   OptimizeFor: Optimize for print quality
            doc.ExportAsFixedFormat(
                OutputFileName=str(target.absolute()),
                ExportFormat=WD_EXPORT_FORMAT_PDF,
                OpenAfterExport=False,
                OptimizeFor=WD_EXPORT_OPTIMIZE_FOR_PRINT,
            )
            
            # ===================================================================
            # STEP 6: Get Page Count for Statistics
            # ===================================================================
            # ComputeStatistics(2) returns page count
            # 2 = wdStatisticPages constant
            page_count = doc.ComputeStatistics(2)
            
            # ===================================================================
            # STEP 7: Close Document and Word
            # ===================================================================
            # Close document without saving changes (False)
            doc.Close(False)
            doc = None  # Clear reference
            
            # Quit Word application
            word.Quit()
            word = None  # Clear reference
            
            # ===================================================================
            # STEP 8: Return Success Result
            # ===================================================================
            duration = time.time() - start_time
            self._logger.info(
                f"Word conversion complete: {target.name} "
                f"({page_count} pages, {duration:.1f}s)"
            )
            
            return ConversionResult(
                success=True,
                source_path=source,
                output_path=target,
                duration_seconds=duration,
                pages=page_count,
            )
            
        except Exception as e:
            # ===================================================================
            # ERROR HANDLING: Clean up and return failure
            # ===================================================================
            self._logger.error(f"Word conversion failed: {e}")
            
            # Attempt to close document if open
            if doc is not None:
                try:
                    doc.Close(False)
                except Exception:
                    pass  # Ignore errors during cleanup
            
            # Attempt to quit Word if running
            if word is not None:
                try:
                    word.Quit()
                except Exception:
                    pass
            
            return ConversionResult(
                success=False,
                source_path=source,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )
