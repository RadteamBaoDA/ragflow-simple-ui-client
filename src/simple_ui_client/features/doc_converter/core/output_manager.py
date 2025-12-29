"""
Output manager for document conversion.

Handles output file organization, folder structure preservation,
suffix mapping, temp file management, and summary report generation.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from simple_ui_client.features.doc_converter.config import SuffixConfig


class FileType(str, Enum):
    """Document file types."""
    WORD = "word"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    UNKNOWN = "unknown"


# File extension mappings
WORD_EXTENSIONS = {".doc", ".docx", ".rtf", ".odt"}
EXCEL_EXTENSIONS = {".xls", ".xlsx", ".xlsm", ".xlsb", ".ods", ".csv"}
POWERPOINT_EXTENSIONS = {".ppt", ".pptx", ".odp"}
MACRO_EXCEL_EXTENSIONS = {".xlsm", ".xlsb", ".xltm"}


@dataclass
class ConversionError:
    """Details of a conversion error."""
    source_path: Path
    error_message: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConversionSummary:
    """Summary of a conversion batch."""
    start_time: datetime
    end_time: datetime | None = None
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    errors: list[ConversionError] = field(default_factory=list)
    output_dir: Path | None = None


class OutputManager:
    """
    Manages output files for document conversion.
    
    Features:
    - Preserves input folder structure in output
    - Applies configurable file suffixes
    - Manages temporary files
    - Generates summary reports with error details
    """
    
    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        suffix_config: "SuffixConfig",
        keep_temp: bool = False,
    ) -> None:
        """
        Initialize the output manager.
        
        Args:
            input_dir: Base input directory.
            output_dir: Base output directory.
            suffix_config: File suffix configuration.
            keep_temp: Whether to keep temporary files.
        """
        self.input_dir = input_dir.resolve()
        self.output_dir = output_dir.resolve()
        self.suffix_config = suffix_config
        self.keep_temp = keep_temp
        
        self._temp_files: list[Path] = []
        self._summary = ConversionSummary(start_time=datetime.now())
        self._logger = logger.bind(component="OutputManager")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_file_type(path: Path) -> FileType:
        """Determine the file type from extension."""
        ext = path.suffix.lower()
        
        if ext in WORD_EXTENSIONS:
            return FileType.WORD
        elif ext in EXCEL_EXTENSIONS:
            return FileType.EXCEL
        elif ext in POWERPOINT_EXTENSIONS:
            return FileType.POWERPOINT
        else:
            return FileType.UNKNOWN
    
    @staticmethod
    def is_macro_excel(path: Path) -> bool:
        """Check if the file is a macro-enabled Excel file."""
        return path.suffix.lower() in MACRO_EXCEL_EXTENSIONS
    
    def get_suffix(self, file_type: FileType) -> str:
        """Get the suffix for a file type."""
        suffixes = {
            FileType.WORD: self.suffix_config.word,
            FileType.EXCEL: self.suffix_config.excel,
            FileType.POWERPOINT: self.suffix_config.powerpoint,
        }
        return suffixes.get(file_type, "")
    
    def get_output_path(self, source_path: Path) -> Path:
        """
        Calculate output path preserving folder structure.
        
        Args:
            source_path: Path to source file.
            
        Returns:
            Path for the output PDF.
        """
        # Get relative path from input directory
        try:
            relative = source_path.resolve().relative_to(self.input_dir)
        except ValueError:
            # Source is not under input_dir, use just the filename
            relative = Path(source_path.name)
        
        # Get file type and suffix
        file_type = self.get_file_type(source_path)
        suffix = self.get_suffix(file_type)
        
        # Create output path: preserve structure, change name and extension
        output_name = f"{source_path.stem}{suffix}.pdf"
        output_path = self.output_dir / relative.parent / output_name
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        return output_path
    
    def get_temp_path(self, source_path: Path, extension: str = ".xlsx") -> Path:
        """
        Get a temporary file path.
        
        Args:
            source_path: Original source path.
            extension: Desired extension for temp file.
            
        Returns:
            Path for temporary file.
        """
        temp_dir = self.output_dir / ".temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        temp_path = temp_dir / f"{source_path.stem}_temp{extension}"
        self._temp_files.append(temp_path)
        
        return temp_path
    
    def record_success(self, source_path: Path) -> None:
        """Record a successful conversion."""
        self._summary.successful += 1
        self._summary.total_files += 1
    
    def record_error(self, source_path: Path, error_message: str) -> None:
        """Record a conversion error."""
        self._summary.failed += 1
        self._summary.total_files += 1
        self._summary.errors.append(ConversionError(
            source_path=source_path,
            error_message=error_message,
        ))
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary files if configured."""
        if self.keep_temp:
            self._logger.info(f"Keeping {len(self._temp_files)} temporary files")
            return
        
        for temp_path in self._temp_files:
            try:
                if temp_path.exists():
                    temp_path.unlink()
                    self._logger.debug(f"Deleted temp file: {temp_path}")
            except Exception as e:
                self._logger.warning(f"Failed to delete temp file {temp_path}: {e}")
        
        # Try to remove temp directory if empty
        temp_dir = self.output_dir / ".temp"
        if temp_dir.exists():
            try:
                temp_dir.rmdir()
            except OSError:
                pass  # Directory not empty
        
        self._temp_files.clear()
    
    def generate_summary_report(self) -> Path:
        """
        Generate a summary report file.
        
        Returns:
            Path to the generated summary file.
        """
        self._summary.end_time = datetime.now()
        self._summary.output_dir = self.output_dir
        
        # Generate filename with timestamp
        timestamp = self._summary.start_time.strftime("%Y%m%d%H%M%S")
        report_path = self.output_dir / f"summary_{timestamp}.txt"
        
        # Build report content
        lines = [
            "=" * 60,
            "DOCUMENT CONVERSION SUMMARY REPORT",
            "=" * 60,
            "",
            f"Start Time:    {self._summary.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"End Time:      {self._summary.end_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration:      {(self._summary.end_time - self._summary.start_time).total_seconds():.1f} seconds",
            "",
            f"Total Files:   {self._summary.total_files}",
            f"Successful:    {self._summary.successful}",
            f"Failed:        {self._summary.failed}",
            "",
            f"Output Dir:    {self._summary.output_dir}",
            "",
        ]
        
        if self._summary.errors:
            lines.extend([
                "-" * 60,
                "ERRORS",
                "-" * 60,
                "",
            ])
            
            for error in self._summary.errors:
                lines.extend([
                    f"File: {error.source_path}",
                    f"Error: {error.error_message}",
                    f"Time: {error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                    "",
                ])
        else:
            lines.extend([
                "-" * 60,
                "No errors occurred.",
                "-" * 60,
            ])
        
        lines.append("")
        lines.append("=" * 60)
        
        # Write report
        report_path.write_text("\n".join(lines), encoding="utf-8")
        
        self._logger.info(f"Summary report generated: {report_path}")
        
        return report_path
    
    def get_summary(self) -> ConversionSummary:
        """Get the current conversion summary."""
        self._summary.end_time = datetime.now()
        return self._summary


def discover_files(input_dir: Path, recursive: bool = True) -> list[Path]:
    """
    Discover Office documents in a directory.
    
    Args:
        input_dir: Directory to search.
        recursive: Whether to search recursively.
        
    Returns:
        List of Office document paths.
    """
    all_extensions = WORD_EXTENSIONS | EXCEL_EXTENSIONS | POWERPOINT_EXTENSIONS
    
    files: list[Path] = []
    
    if recursive:
        for ext in all_extensions:
            files.extend(input_dir.rglob(f"*{ext}"))
    else:
        for ext in all_extensions:
            files.extend(input_dir.glob(f"*{ext}"))
    
    # Sort by path for consistent ordering
    files.sort()
    
    return files
