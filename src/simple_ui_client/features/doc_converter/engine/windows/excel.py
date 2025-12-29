"""
Windows Office 365 COM Engine - Excel Converter Module.

This module handles conversion of Excel spreadsheets (.xls, .xlsx, .xlsm)
to PDF format using Microsoft Excel through COM automation on Windows.

Excel COM provides full access to all print and page setup features,
including:
- Scaling options (fit to page, percentage)
- Headers and footers
- Page breaks
- Margins and orientation
- Sheet-specific settings

Requirements:
    - Microsoft Office 365 or Office 2016+ installed
    - pywin32 package (pip install pywin32)

Author: Simple UI Team
Created: December 2024
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from simple_ui_client.features.doc_converter.engine.base import ConversionResult

if TYPE_CHECKING:
    from simple_ui_client.features.doc_converter.config import (
        ExcelPrintConfig,
        MarginType,
        ScalingMode,
    )


# ============================================================================
# Excel COM Constants
# ============================================================================
# Reference: https://docs.microsoft.com/en-us/office/vba/api/excel.xlsheettype

# PDF export type constant
XL_TYPE_PDF = 0

# PDF quality settings
XL_QUALITY_STANDARD = 0
XL_QUALITY_MINIMUM = 1

# Page orientation
XL_PORTRAIT = 1
XL_LANDSCAPE = 2

# File format for XLSX (when converting XLSM)
XL_OPENXML_WORKBOOK = 51  # .xlsx format


class WindowsExcelConverter:
    """
    Converts Excel spreadsheets to PDF using Microsoft Excel COM automation.
    
    This converter provides full access to Excel's page setup features:
    - Scaling: fit sheet, fit columns, fit rows, percentage
    - Margins: all margins including header/footer
    - Headers/Footers: custom text with sheet name, page numbers
    - Page breaks: automatic and manual
    - Print area and titles
    
    Supported formats:
        - .xls   (Legacy Excel 97-2003)
        - .xlsx  (Modern Excel, Office 2007+)
        - .xlsm  (Excel with macros - fully supported)
        - .xlsb  (Binary Excel format)
    
    Threading:
        - Initialize COM before use (one per thread)
        - Excel instances should not be shared between threads
        - Each thread gets its own Excel process
    
    Example:
        converter = WindowsExcelConverter()
        converter.initialize()
        try:
            result = converter.convert(source, target, config)
        finally:
            converter.cleanup()
    """
    
    def __init__(self) -> None:
        """Initialize the Excel converter."""
        self._initialized = False
        self._logger = logger.bind(component="WindowsExcelConverter")
    
    def initialize(self) -> None:
        """
        Initialize COM for Excel operations.
        
        Must be called from the worker thread before conversion.
        Sets up COM single-threaded apartment for this thread.
        """
        if self._initialized:
            return
        
        try:
            import pythoncom
            pythoncom.CoInitialize()
            self._initialized = True
            self._logger.debug("COM initialized for Excel converter")
        except ImportError:
            raise RuntimeError("pywin32 package required")
        except Exception as e:
            raise RuntimeError(f"COM initialization failed: {e}")
    
    def cleanup(self) -> None:
        """
        Clean up COM resources.
        
        Must be called from the same thread that called initialize().
        """
        if not self._initialized:
            return
        
        try:
            import pythoncom
            pythoncom.CoUninitialize()
            self._initialized = False
            self._logger.debug("COM uninitialized for Excel converter")
        except Exception as e:
            self._logger.warning(f"Error during COM cleanup: {e}")
    
    def _get_margin_inches(self, margin_type: "MarginType") -> tuple[float, float, float, float]:
        """Get margin values for a preset."""
        from simple_ui_client.features.doc_converter.config import MarginType
        
        presets = {
            MarginType.NORMAL: (0.75, 0.75, 0.7, 0.7),
            MarginType.NARROW: (0.5, 0.5, 0.5, 0.5),
            MarginType.WIDE: (1.0, 1.0, 1.0, 1.0),
        }
        return presets.get(margin_type, presets[MarginType.NORMAL])
    
    def convert(
        self,
        source: Path,
        target: Path,
        config: "ExcelPrintConfig",
        sheet_name: str | None = None,
    ) -> ConversionResult:
        """
        Convert an Excel spreadsheet to PDF.
        
        This method:
        1. Opens workbook in Excel (invisible)
        2. Applies page setup to all or specific sheets
        3. Sets up scaling, margins, headers
        4. Exports to PDF
        5. Closes Excel
        
        Args:
            source: Path to Excel file (.xls, .xlsx, .xlsm).
            target: Output path for PDF file.
            config: Excel print configuration with:
                   - scaling: 'no_scaling', 'fit_sheet', 'fit_columns', 'fit_rows', 'custom'
                   - scaling_percent: Percentage when scaling='custom' (1-400)
                   - margins: 'normal', 'narrow', 'wide', 'custom'
                   - print_header_footer: Show sheet name and page numbers
                   - print_row_col_headings: Show Excel row/column labels
                   - rows_per_page: Add page breaks every N rows
                   - columns_per_page: Add page breaks every N columns
                   - orientation: 'portrait' or 'landscape'
            sheet_name: Optional specific sheet to convert.
                       If None, all sheets are included.
        
        Returns:
            ConversionResult with conversion details.
        """
        start_time = time.time()
        excel = None
        workbook = None
        
        try:
            import win32com.client
            from simple_ui_client.features.doc_converter.config import (
                MarginType,
                Orientation,
                ScalingMode,
            )
            
            self._logger.info(f"Converting Excel spreadsheet: {source.name}")
            
            # ===================================================================
            # STEP 1: Create Excel Application Instance
            # ===================================================================
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False           # Hide Excel window
            excel.DisplayAlerts = False     # Suppress all dialogs
            excel.ScreenUpdating = False    # Improve performance
            
            # ===================================================================
            # STEP 2: Open the Workbook
            # ===================================================================
            workbook = excel.Workbooks.Open(str(source.absolute()))
            
            # ===================================================================
            # STEP 3: Configure Each Worksheet
            # ===================================================================
            for sheet in workbook.Worksheets:
                # Skip sheets we're not converting (if specific sheet requested)
                if sheet_name and sheet.Name != sheet_name:
                    continue
                
                # Get page setup object for this sheet
                ps = sheet.PageSetup
                
                # ---------------------------------------------------------
                # Orientation Setting
                # ---------------------------------------------------------
                if config.orientation == Orientation.LANDSCAPE:
                    ps.Orientation = XL_LANDSCAPE
                else:
                    ps.Orientation = XL_PORTRAIT
                
                # ---------------------------------------------------------
                # Margin Settings
                # ---------------------------------------------------------
                if config.margins == MarginType.CUSTOM:
                    # Custom margins from config (in inches, converted to points)
                    ps.TopMargin = excel.InchesToPoints(config.margins_custom.top)
                    ps.BottomMargin = excel.InchesToPoints(config.margins_custom.bottom)
                    ps.LeftMargin = excel.InchesToPoints(config.margins_custom.left)
                    ps.RightMargin = excel.InchesToPoints(config.margins_custom.right)
                    ps.HeaderMargin = excel.InchesToPoints(config.margins_custom.header)
                    ps.FooterMargin = excel.InchesToPoints(config.margins_custom.footer)
                else:
                    # Use preset margins
                    top, bottom, left, right = self._get_margin_inches(config.margins)
                    ps.TopMargin = excel.InchesToPoints(top)
                    ps.BottomMargin = excel.InchesToPoints(bottom)
                    ps.LeftMargin = excel.InchesToPoints(left)
                    ps.RightMargin = excel.InchesToPoints(right)
                
                # ---------------------------------------------------------
                # Scaling Settings
                # ---------------------------------------------------------
                # Excel scaling works with Zoom OR FitToPages, not both
                
                if config.scaling == ScalingMode.FIT_SHEET:
                    # Fit entire sheet on one page
                    ps.Zoom = False          # Disable percentage zoom
                    ps.FitToPagesWide = 1    # One page wide
                    ps.FitToPagesTall = 1    # One page tall
                    
                elif config.scaling == ScalingMode.FIT_COLUMNS:
                    # Fit all columns on page width, any number of rows
                    ps.Zoom = False
                    ps.FitToPagesWide = 1
                    ps.FitToPagesTall = False  # Unlimited pages tall
                    
                elif config.scaling == ScalingMode.FIT_ROWS:
                    # Fit all rows on page height, any number of columns
                    ps.Zoom = False
                    ps.FitToPagesWide = False
                    ps.FitToPagesTall = 1
                    
                elif config.scaling == ScalingMode.CUSTOM:
                    # Use specific percentage (10-400%)
                    ps.Zoom = config.scaling_percent
                    ps.FitToPagesWide = False
                    ps.FitToPagesTall = False
                    
                else:  # NO_SCALING
                    ps.Zoom = 100
                    ps.FitToPagesWide = False
                    ps.FitToPagesTall = False
                
                # ---------------------------------------------------------
                # Header/Footer Settings
                # ---------------------------------------------------------
                if config.print_header_footer:
                    # &A = Sheet name, &P = Current page, &N = Total pages
                    ps.CenterHeader = "&A"           # Sheet name centered
                    ps.RightHeader = "Page &P of &N" # Page numbers on right
                    ps.LeftHeader = ""
                    ps.CenterFooter = ""
                    ps.LeftFooter = ""
                    ps.RightFooter = ""
                else:
                    # Clear all headers and footers
                    ps.CenterHeader = ""
                    ps.RightHeader = ""
                    ps.LeftHeader = ""
                    ps.CenterFooter = ""
                    ps.RightFooter = ""
                    ps.LeftFooter = ""
                
                # ---------------------------------------------------------
                # Row/Column Headings
                # ---------------------------------------------------------
                # PrintHeadings shows Excel's row numbers (1,2,3) and
                # column letters (A,B,C) in the printout
                ps.PrintHeadings = config.print_row_col_headings
                
                # ---------------------------------------------------------
                # Page Break Settings
                # ---------------------------------------------------------
                if config.rows_per_page:
                    # Add horizontal page breaks every N rows
                    used_range = sheet.UsedRange
                    total_rows = used_range.Rows.Count
                    
                    # First, clear existing page breaks
                    sheet.ResetAllPageBreaks()
                    
                    # Add breaks at regular intervals
                    for row in range(
                        config.rows_per_page + 1,  # Start after first block
                        total_rows + 1,            # Go to end of data
                        config.rows_per_page       # Step by rows_per_page
                    ):
                        # HPageBreaks = Horizontal Page Breaks (between rows)
                        sheet.HPageBreaks.Add(Before=sheet.Rows(row))
                
                if config.columns_per_page:
                    # Add vertical page breaks every N columns
                    used_range = sheet.UsedRange
                    total_cols = used_range.Columns.Count
                    
                    for col in range(
                        config.columns_per_page + 1,
                        total_cols + 1,
                        config.columns_per_page
                    ):
                        # VPageBreaks = Vertical Page Breaks (between columns)
                        sheet.VPageBreaks.Add(Before=sheet.Columns(col))
            
            # ===================================================================
            # STEP 4: Create Output Directory
            # ===================================================================
            target.parent.mkdir(parents=True, exist_ok=True)
            
            # ===================================================================
            # STEP 5: Export to PDF
            # ===================================================================
            if sheet_name:
                # Export specific sheet only
                sheet = workbook.Worksheets(sheet_name)
                sheet.ExportAsFixedFormat(
                    Type=XL_TYPE_PDF,
                    Filename=str(target.absolute()),
                    Quality=XL_QUALITY_STANDARD,
                )
            else:
                # Export entire workbook (all sheets)
                workbook.ExportAsFixedFormat(
                    Type=XL_TYPE_PDF,
                    Filename=str(target.absolute()),
                    Quality=XL_QUALITY_STANDARD,
                )
            
            # ===================================================================
            # STEP 6: Close and Cleanup
            # ===================================================================
            workbook.Close(SaveChanges=False)  # Don't save changes
            workbook = None
            
            excel.Quit()
            excel = None
            
            # ===================================================================
            # STEP 7: Return Success
            # ===================================================================
            duration = time.time() - start_time
            self._logger.info(f"Excel conversion complete: {target.name} ({duration:.1f}s)")
            
            return ConversionResult(
                success=True,
                source_path=source,
                output_path=target,
                duration_seconds=duration,
            )
            
        except Exception as e:
            self._logger.error(f"Excel conversion failed: {e}")
            
            # Cleanup on error
            if workbook:
                try:
                    workbook.Close(False)
                except Exception:
                    pass
            if excel:
                try:
                    excel.Quit()
                except Exception:
                    pass
            
            return ConversionResult(
                success=False,
                source_path=source,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )
    
    def convert_xlsm_to_xlsx(
        self,
        source: Path,
        target: Path,
    ) -> ConversionResult:
        """
        Convert macro-enabled Excel file to standard XLSX.
        
        This removes VBA macros while preserving:
        - All cell data and formulas
        - Formatting and styles
        - Charts and images
        - Pivot tables
        - Named ranges
        
        Use case: Some systems can't process XLSM files,
        or you want to remove macros for security.
        
        Args:
            source: Path to XLSM/XLSB file.
            target: Path for output XLSX file.
        
        Returns:
            ConversionResult indicating success/failure.
        """
        start_time = time.time()
        excel = None
        workbook = None
        
        try:
            import win32com.client
            
            self._logger.info(f"Converting to XLSX: {source.name}")
            
            # Create Excel instance
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            
            # Open macro file
            workbook = excel.Workbooks.Open(str(source.absolute()))
            
            # Ensure output directory exists
            target.parent.mkdir(parents=True, exist_ok=True)
            
            # Save as XLSX (FileFormat=51 removes macros)
            workbook.SaveAs(
                Filename=str(target.absolute()),
                FileFormat=XL_OPENXML_WORKBOOK  # 51 = .xlsx
            )
            
            workbook.Close(SaveChanges=False)
            workbook = None
            
            excel.Quit()
            excel = None
            
            duration = time.time() - start_time
            self._logger.info(f"XLSX conversion complete: {target.name}")
            
            return ConversionResult(
                success=True,
                source_path=source,
                output_path=target,
                duration_seconds=duration,
            )
            
        except Exception as e:
            self._logger.error(f"XLSM to XLSX conversion failed: {e}")
            
            if workbook:
                try:
                    workbook.Close(False)
                except Exception:
                    pass
            if excel:
                try:
                    excel.Quit()
                except Exception:
                    pass
            
            return ConversionResult(
                success=False,
                source_path=source,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )
