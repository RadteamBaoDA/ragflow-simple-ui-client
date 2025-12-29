"""
Linux LibreOffice Engine - Word Converter Module.

This module handles conversion of Word documents (.doc, .docx, .rtf, .odt)
to PDF format using LibreOffice in headless mode on Linux systems.

LibreOffice is called via subprocess with the --headless flag, which allows
it to run without a graphical interface, making it suitable for server
environments and automated processing.

Author: RAGFlow Team
Created: December 2024
"""

from __future__ import annotations

# Standard library imports for file and process handling
import subprocess  # Used to run LibreOffice as an external process
import time       # Used to measure conversion duration
from pathlib import Path  # Modern way to handle file paths cross-platform
from typing import TYPE_CHECKING  # Used for type hints without runtime import

# Third-party logging library - provides structured, colorful logging
from loguru import logger

# Import our base class and result type from the parent module
from ragflow_client.features.doc_converter.engine.base import ConversionResult

# TYPE_CHECKING is True only when running type checkers (like mypy),
# not at runtime. This avoids circular imports for type hints.
if TYPE_CHECKING:
    from ragflow_client.features.doc_converter.converter_config import WordConfig


class LinuxWordConverter:
    """
    Converts Word documents to PDF using LibreOffice on Linux.
    
    LibreOffice provides excellent compatibility with Microsoft Word formats
    and can run in headless mode for server/batch processing.
    
    Supported formats:
        - .doc  (Legacy Word 97-2003 format)
        - .docx (Modern Word format, Office 2007+)
        - .rtf  (Rich Text Format)
        - .odt  (OpenDocument Text - LibreOffice native format)
    
    Example usage:
        converter = LinuxWordConverter()
        result = converter.convert(
            source=Path("/path/to/document.docx"),
            target=Path("/path/to/output.pdf"),
            config=word_config
        )
        if result.success:
            print(f"Converted to: {result.output_path}")
    """
    
    def __init__(self, libreoffice_path: str = "libreoffice") -> None:
        """
        Initialize the Word converter.
        
        Args:
            libreoffice_path: Path or command name for LibreOffice executable.
                            Default is "libreoffice" which works if it's in PATH.
                            Can be full path like "/usr/bin/libreoffice" if needed.
        """
        # Store the LibreOffice path for later use
        self._libreoffice = libreoffice_path
        
        # Create a logger with context - helps identify log sources
        # The 'component' field will appear in log output for filtering
        self._logger = logger.bind(component="LinuxWordConverter")
    
    def convert(
        self,
        source: Path,
        target: Path,
        config: "WordConfig",
        timeout: int = 300,
    ) -> ConversionResult:
        """
        Convert a Word document to PDF.
        
        This method:
        1. Validates that source exists
        2. Creates output directory if needed
        3. Runs LibreOffice in headless mode to convert
        4. Renames the output file to match the target path
        
        Args:
            source: Path to the input Word document.
                    Must be an existing file with .doc/.docx/.rtf/.odt extension.
            target: Desired path for the output PDF file.
                    Parent directory will be created if it doesn't exist.
            config: Word print configuration (margins, orientation, etc.).
                   Note: LibreOffice has limited support for Word print settings.
            timeout: Maximum time in seconds to wait for conversion.
                    Default 300 seconds (5 minutes) is usually enough.
        
        Returns:
            ConversionResult object containing:
                - success: True if conversion succeeded
                - source_path: The input file path
                - output_path: The output PDF path (if successful)
                - error: Error message (if failed)
                - duration_seconds: Time taken for conversion
        
        Raises:
            No exceptions are raised - all errors are captured in the result.
        """
        # Record start time to measure conversion duration
        start_time = time.time()
        
        try:
            # Log the operation start for debugging and monitoring
            self._logger.info(f"Converting Word document: {source.name}")
            
            # ===================================================================
            # STEP 1: Prepare the output directory
            # ===================================================================
            # LibreOffice outputs files to a directory, not a specific filename.
            # We get the parent directory of our target path.
            output_dir = target.parent
            
            # Create the directory if it doesn't exist
            # parents=True: Create parent directories too (like mkdir -p)
            # exist_ok=True: Don't error if directory already exists
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # ===================================================================
            # STEP 2: Build the LibreOffice command
            # ===================================================================
            # LibreOffice command-line arguments explained:
            # --headless     : Run without GUI (required for servers)
            # --invisible    : Don't show splash screen or UI elements
            # --nologo       : Skip the logo/splash screen entirely
            # --nofirststartwizard : Skip first-run setup wizard
            # --convert-to pdf     : Output format specification
            # --outdir <dir>       : Directory for output files
            # <input_file>         : The file to convert (last argument)
            args = [
                self._libreoffice,     # The LibreOffice executable
                "--headless",          # No GUI - essential for server use
                "--invisible",         # Extra invisibility flag
                "--nologo",            # Skip logo screen
                "--nofirststartwizard",  # Skip setup wizard
                "--convert-to", "pdf",  # Convert to PDF format
                "--outdir", str(output_dir),  # Output directory
                str(source),           # Input file path
            ]
            
            # ===================================================================
            # STEP 3: Execute LibreOffice conversion
            # ===================================================================
            # subprocess.run() executes the command and waits for completion
            result = subprocess.run(
                args,                  # The command and arguments
                capture_output=True,   # Capture stdout and stderr
                text=True,             # Return output as strings, not bytes
                timeout=timeout,       # Maximum wait time in seconds
            )
            
            # ===================================================================
            # STEP 4: Check for conversion errors
            # ===================================================================
            # A non-zero return code indicates failure
            if result.returncode != 0:
                # Get error message from stderr or stdout (LibreOffice may use either)
                error = result.stderr or result.stdout or "Unknown LibreOffice error"
                self._logger.error(f"LibreOffice failed: {error}")
                
                # Return failure result with error details
                return ConversionResult(
                    success=False,
                    source_path=source,
                    error=error,
                    duration_seconds=time.time() - start_time,
                )
            
            # ===================================================================
            # STEP 5: Handle output file naming
            # ===================================================================
            # LibreOffice creates output with the same base name but .pdf extension
            # For example: document.docx -> document.pdf
            generated_pdf = output_dir / f"{source.stem}.pdf"
            
            # If the generated filename differs from our target, rename it
            # This allows users to specify custom output names like "report_final.pdf"
            if generated_pdf != target and generated_pdf.exists():
                generated_pdf.rename(target)
            
            # ===================================================================
            # STEP 6: Return success result
            # ===================================================================
            duration = time.time() - start_time
            self._logger.info(
                f"Word conversion complete: {target.name} ({duration:.1f}s)"
            )
            
            return ConversionResult(
                success=True,
                source_path=source,
                output_path=target,
                duration_seconds=duration,
            )
            
        except subprocess.TimeoutExpired:
            # Handle case where LibreOffice takes too long
            self._logger.error(f"Conversion timed out after {timeout}s: {source.name}")
            return ConversionResult(
                success=False,
                source_path=source,
                error=f"Conversion timed out after {timeout} seconds",
                duration_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            # Catch any unexpected errors (file permission issues, etc.)
            self._logger.error(f"Word conversion failed: {e}")
            return ConversionResult(
                success=False,
                source_path=source,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )
