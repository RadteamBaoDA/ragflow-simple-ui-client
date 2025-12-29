"""
Linux LibreOffice Engine - PowerPoint Converter Module.

This module handles conversion of PowerPoint presentations (.ppt, .pptx, .odp)
to PDF format using LibreOffice Impress in headless mode on Linux systems.

LibreOffice Impress provides good compatibility with PowerPoint formats
and preserves slide layouts, animations (as static), and formatting.

Author: RAGFlow Team
Created: December 2024
"""

from __future__ import annotations

# Standard library imports
import subprocess  # Execute LibreOffice as external process
import time       # Measure conversion duration
from pathlib import Path  # Modern path handling
from typing import TYPE_CHECKING  # Type hints without runtime overhead

# Structured logging
from loguru import logger

# Base result type
from ragflow_client.features.doc_converter.engine.base import ConversionResult

if TYPE_CHECKING:
    from ragflow_client.features.doc_converter.config import PowerPointConfig


class LinuxPowerPointConverter:
    """
    Converts PowerPoint presentations to PDF using LibreOffice Impress on Linux.
    
    LibreOffice Impress handles most PowerPoint features well:
    - Slide layouts and themes
    - Text formatting and fonts
    - Images and shapes
    - Charts and tables
    - Transitions (converted to static slides)
    
    Animations are not preserved - each slide becomes a static page.
    
    Supported formats:
        - .ppt   (Legacy PowerPoint 97-2003)
        - .pptx  (Modern PowerPoint, Office 2007+)
        - .ppsx  (PowerPoint Show - auto-play format)
        - .odp   (OpenDocument Presentation - LibreOffice native)
    
    Example:
        converter = LinuxPowerPointConverter()
        result = converter.convert(
            source=Path("/presentations/slides.pptx"),
            target=Path("/output/slides.pdf"),
            config=ppt_config
        )
    """
    
    def __init__(self, libreoffice_path: str = "libreoffice") -> None:
        """
        Initialize the PowerPoint converter.
        
        Args:
            libreoffice_path: Path or command name for LibreOffice.
                            Default "libreoffice" requires it to be in PATH.
        """
        self._libreoffice = libreoffice_path
        self._logger = logger.bind(component="LinuxPowerPointConverter")
    
    def convert(
        self,
        source: Path,
        target: Path,
        config: "PowerPointConfig",
        timeout: int = 300,
    ) -> ConversionResult:
        """
        Convert a PowerPoint presentation to PDF.
        
        Each slide in the presentation becomes one page in the PDF.
        Animations and transitions are not preserved - slides are
        captured in their final state.
        
        The conversion process:
        1. Validate input file
        2. Create output directory
        3. Run LibreOffice Impress headless conversion
        4. Rename output to match target path
        
        Args:
            source: Path to the PowerPoint file.
                   Supports .ppt, .pptx, .ppsx, .odp formats.
            target: Desired output path for the PDF.
                   Directory will be created if needed.
            config: PowerPoint configuration options.
                   Note: LibreOffice has limited support for:
                   - Handout layouts (not supported)
                   - Slide size changes (not supported)
                   The PDF will match the original slide dimensions.
            timeout: Maximum time to wait for conversion (seconds).
                    Most presentations convert in under a minute.
                    Default 300 seconds (5 minutes).
        
        Returns:
            ConversionResult containing:
                - success: Boolean indicating success/failure
                - source_path: Original input path
                - output_path: PDF path (if successful)
                - error: Error message (if failed)
                - duration_seconds: Conversion time
        """
        start_time = time.time()
        
        try:
            self._logger.info(f"Converting PowerPoint: {source.name}")
            
            # ===================================================================
            # STEP 1: Log configuration info
            # ===================================================================
            # Note: LibreOffice Impress PDF export has fewer options than
            # PowerPoint COM automation. We log the config but can only
            # do a basic conversion.
            self._logger.debug(
                f"PowerPoint config: output_type={config.output_type}, "
                f"include_hidden={config.include_hidden}"
            )
            
            # ===================================================================
            # STEP 2: Prepare output directory
            # ===================================================================
            output_dir = target.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # ===================================================================
            # STEP 3: Build the LibreOffice command
            # ===================================================================
            # LibreOffice Impress uses the same command-line interface
            # as other LibreOffice applications. The output format is
            # determined by the --convert-to argument.
            args = [
                self._libreoffice,
                "--headless",           # Run without GUI
                "--invisible",          # No visible window
                "--nologo",             # Skip splash screen
                "--nofirststartwizard", # Skip setup wizard
                "--convert-to", "pdf",  # Output as PDF
                "--outdir", str(output_dir),  # Output directory
                str(source),            # Input file path
            ]
            
            # ===================================================================
            # STEP 4: Execute the conversion
            # ===================================================================
            self._logger.debug("Starting LibreOffice Impress conversion")
            
            result = subprocess.run(
                args,
                capture_output=True,  # Capture stdout and stderr
                text=True,            # Return as string (not bytes)
                timeout=timeout,      # Wait at most this many seconds
            )
            
            # ===================================================================
            # STEP 5: Check for errors
            # ===================================================================
            if result.returncode != 0:
                # LibreOffice returns non-zero on failure
                error = result.stderr or result.stdout or "Impress conversion failed"
                self._logger.error(f"LibreOffice Impress error: {error}")
                
                return ConversionResult(
                    success=False,
                    source_path=source,
                    error=error,
                    duration_seconds=time.time() - start_time,
                )
            
            # ===================================================================
            # STEP 6: Handle output file name
            # ===================================================================
            # LibreOffice creates "filename.pdf" in the output directory
            generated_pdf = output_dir / f"{source.stem}.pdf"
            
            # Rename to the user's desired target path if different
            if generated_pdf != target and generated_pdf.exists():
                generated_pdf.rename(target)
            
            # ===================================================================
            # STEP 7: Return successful result
            # ===================================================================
            duration = time.time() - start_time
            self._logger.info(
                f"PowerPoint conversion complete: {target.name} ({duration:.1f}s)"
            )
            
            return ConversionResult(
                success=True,
                source_path=source,
                output_path=target,
                duration_seconds=duration,
            )
            
        except subprocess.TimeoutExpired:
            # Handle case where LibreOffice hangs or takes too long
            self._logger.error(f"PowerPoint conversion timed out after {timeout}s")
            return ConversionResult(
                success=False,
                source_path=source,
                error=f"Conversion timed out after {timeout} seconds",
                duration_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            # Catch all other errors (file not found, permissions, etc.)
            self._logger.error(f"PowerPoint conversion failed: {e}")
            return ConversionResult(
                success=False,
                source_path=source,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )
