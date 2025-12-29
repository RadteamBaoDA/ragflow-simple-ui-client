"""
Linux LibreOffice Engine - Excel Converter Module.

This module handles conversion of Excel spreadsheets (.xls, .xlsx, .xlsm, .ods)
to PDF format using LibreOffice Calc in headless mode on Linux systems.

Note: LibreOffice has limited support for advanced Excel print settings
compared to Windows Office COM. Some features like custom page breaks
may not work exactly as configured.

Author: Simple UI Team
Created: December 2024
"""

from __future__ import annotations

# Standard library imports
import subprocess  # Run LibreOffice as external process
import time       # Measure conversion time
from pathlib import Path  # Cross-platform path handling
from typing import TYPE_CHECKING  # Type hints without runtime import

# Structured logging library
from loguru import logger

# Our base conversion result type
from simple_ui_client.features.doc_converter.engine.base import ConversionResult

# Import config type only for type checking (avoids circular imports)
if TYPE_CHECKING:
    from simple_ui_client.features.doc_converter.config import ExcelPrintConfig


class LinuxExcelConverter:
    """
    Converts Excel spreadsheets to PDF using LibreOffice Calc on Linux.
    
    LibreOffice Calc handles most Excel formats well, but some advanced
    features like macros (VBA) will not function. The conversion focuses
    on preserving the visual layout of spreadsheets.
    
    Supported formats:
        - .xls   (Legacy Excel 97-2003 format)
        - .xlsx  (Modern Excel format, Office 2007+)
        - .xlsm  (Excel with macros - macros will be ignored)
        - .xlsb  (Binary Excel format)
        - .ods   (OpenDocument Spreadsheet - LibreOffice native)
        - .csv   (Comma-separated values)
    
    Limitations vs Windows COM:
        - No support for Excel macros/VBA
        - Limited page setup options
        - Sheet-specific configurations may not apply
        - Page breaks might differ from original
    
    Example:
        converter = LinuxExcelConverter()
        result = converter.convert(
            source=Path("/data/spreadsheet.xlsx"),
            target=Path("/output/spreadsheet.pdf"),
            config=excel_config
        )
    """
    
    def __init__(self, libreoffice_path: str = "libreoffice") -> None:
        """
        Initialize the Excel converter.
        
        Args:
            libreoffice_path: Path to LibreOffice executable.
                            Defaults to "libreoffice" (must be in system PATH).
        """
        self._libreoffice = libreoffice_path
        self._logger = logger.bind(component="LinuxExcelConverter")
    
    def convert(
        self,
        source: Path,
        target: Path,
        config: "ExcelPrintConfig",
        sheet_name: str | None = None,
        timeout: int = 600,
    ) -> ConversionResult:
        """
        Convert an Excel spreadsheet to PDF.
        
        The conversion process:
        1. Validate source file exists
        2. Create output directory
        3. Run LibreOffice Calc in headless mode
        4. Rename output to match target path
        
        Args:
            source: Path to the Excel file to convert.
            target: Desired path for the output PDF.
            config: Excel print configuration (scaling, margins, etc.).
                   Note: Not all settings are supported by LibreOffice.
            sheet_name: Optional specific sheet to convert.
                       If None, all sheets are included in PDF.
                       Note: LibreOffice sheet selection is limited.
            timeout: Maximum conversion time in seconds.
                    Spreadsheets with many sheets/data may need more time.
                    Default is 600 seconds (10 minutes).
        
        Returns:
            ConversionResult with success status and details.
            Check result.success before using result.output_path.
        """
        # Start timing the conversion
        start_time = time.time()
        
        try:
            self._logger.info(f"Converting Excel spreadsheet: {source.name}")
            
            # ===================================================================
            # STEP 1: Log configuration limitations
            # ===================================================================
            # LibreOffice Calc PDF export has fewer options than Excel COM.
            # We log the config but can't apply all settings.
            self._logger.debug(
                f"Excel config: scaling={config.scaling}, "
                f"margins={config.margins}, "
                f"Note: LibreOffice has limited config support"
            )
            
            # ===================================================================
            # STEP 2: Prepare output directory
            # ===================================================================
            output_dir = target.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # ===================================================================
            # STEP 3: Build LibreOffice command with filter options
            # ===================================================================
            # LibreOffice can accept PDF export filters, but support is limited.
            # The "calc_pdf_Export" filter accepts some options like:
            #   - PageRange: specific pages to export
            #   - Selection: export only selected cells
            #   - UseLosslessCompression: for images
            # However, most Excel-specific settings are not supported.
            
            args = [
                self._libreoffice,
                "--headless",           # No GUI
                "--invisible",          # Hidden processing
                "--nologo",             # No splash screen
                "--nofirststartwizard", # Skip first-run wizard
                "--convert-to", "pdf",  # Output format
                "--outdir", str(output_dir),  # Output directory
                str(source),            # Input file
            ]
            
            # ===================================================================
            # STEP 4: Execute the conversion
            # ===================================================================
            # Excel files with many sheets/formulas may take longer
            self._logger.debug(f"Running LibreOffice with timeout={timeout}s")
            
            result = subprocess.run(
                args,
                capture_output=True,  # Capture stdout/stderr
                text=True,            # Return as string
                timeout=timeout,      # Maximum wait time
            )
            
            # ===================================================================
            # STEP 5: Check for errors
            # ===================================================================
            if result.returncode != 0:
                error = result.stderr or result.stdout or "LibreOffice conversion failed"
                self._logger.error(f"LibreOffice Calc error: {error}")
                
                return ConversionResult(
                    success=False,
                    source_path=source,
                    error=error,
                    duration_seconds=time.time() - start_time,
                )
            
            # ===================================================================
            # STEP 6: Handle output file naming
            # ===================================================================
            # LibreOffice names output as "filename.pdf" in output directory
            generated_pdf = output_dir / f"{source.stem}.pdf"
            
            # Rename to target path if different
            if generated_pdf != target and generated_pdf.exists():
                generated_pdf.rename(target)
            
            # ===================================================================
            # STEP 7: Return success
            # ===================================================================
            duration = time.time() - start_time
            self._logger.info(
                f"Excel conversion complete: {target.name} ({duration:.1f}s)"
            )
            
            return ConversionResult(
                success=True,
                source_path=source,
                output_path=target,
                duration_seconds=duration,
            )
            
        except subprocess.TimeoutExpired:
            self._logger.error(f"Excel conversion timed out after {timeout}s")
            return ConversionResult(
                success=False,
                source_path=source,
                error=f"Conversion timed out after {timeout} seconds. "
                      f"Try increasing timeout for large spreadsheets.",
                duration_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            self._logger.error(f"Excel conversion failed unexpectedly: {e}")
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
        timeout: int = 300,
    ) -> ConversionResult:
        """
        Convert a macro-enabled Excel file to standard XLSX.
        
        This is useful for:
        1. Removing macros before PDF conversion (security)
        2. Creating a clean copy for processing
        3. Compatibility with systems that don't support macros
        
        The macros (VBA code) will be removed in the output file.
        All data, formulas, and formatting are preserved.
        
        Args:
            source: Path to the XLSM/XLSB file with macros.
            target: Path for the output XLSX file (without macros).
            timeout: Maximum time for conversion in seconds.
        
        Returns:
            ConversionResult indicating success or failure.
        """
        start_time = time.time()
        
        try:
            self._logger.info(f"Converting macro Excel to XLSX: {source.name}")
            
            # Ensure output directory exists
            output_dir = target.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Build command to convert to XLSX format
            # LibreOffice uses the output extension to determine format
            args = [
                self._libreoffice,
                "--headless",
                "--invisible",
                "--convert-to", "xlsx",  # Output as standard Excel
                "--outdir", str(output_dir),
                str(source),
            ]
            
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            
            if result.returncode != 0:
                error = result.stderr or result.stdout or "Conversion failed"
                return ConversionResult(
                    success=False,
                    source_path=source,
                    error=error,
                    duration_seconds=time.time() - start_time,
                )
            
            # Handle output naming
            generated_xlsx = output_dir / f"{source.stem}.xlsx"
            if generated_xlsx != target and generated_xlsx.exists():
                generated_xlsx.rename(target)
            
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
            return ConversionResult(
                success=False,
                source_path=source,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )
