"""
Configuration module for document converter.

Loads and validates YAML configuration for Word, Excel, and PowerPoint
print settings using Pydantic models.
"""

from __future__ import annotations

import fnmatch
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================

class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Orientation(str, Enum):
    """Page orientation."""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class MarginType(str, Enum):
    """Margin presets."""
    NORMAL = "normal"
    NARROW = "narrow"
    WIDE = "wide"
    CUSTOM = "custom"


class ScalingMode(str, Enum):
    """Excel scaling modes."""
    NO_SCALING = "no_scaling"
    FIT_SHEET = "fit_sheet"
    FIT_COLUMNS = "fit_columns"
    FIT_ROWS = "fit_rows"
    CUSTOM = "custom"


class PrintMode(str, Enum):
    """Excel print modes."""
    ONE_PAGE = "one_page"
    SCREEN_OPTIMIZED = "screen_optimized"


class SlideSize(str, Enum):
    """PowerPoint slide sizes."""
    WIDESCREEN = "widescreen"
    STANDARD = "standard"
    CUSTOM = "custom"


class OutputType(str, Enum):
    """PowerPoint output types."""
    SLIDES = "slides"
    HANDOUTS = "handouts"
    NOTES = "notes"
    OUTLINE = "outline"


# ============================================================================
# Custom Margins
# ============================================================================

class CustomMargins(BaseModel):
    """Custom margin settings in inches."""
    top: float = 1.0
    bottom: float = 1.0
    left: float = 1.25
    right: float = 1.25
    header: float = 0.3
    footer: float = 0.3


# ============================================================================
# Logging Config
# ============================================================================

class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: LogLevel = LogLevel.INFO
    log_dir: Path = Path("./logs")
    log_console_lines: int = Field(default=20, ge=5, le=100)


# ============================================================================
# Conversion Config
# ============================================================================

class SuffixConfig(BaseModel):
    """File suffix mappings for output PDFs."""
    word: str = "_d"
    excel: str = "_x"
    powerpoint: str = "_p"


class ConversionConfig(BaseModel):
    """Main conversion settings."""
    workers: int = Field(default=4, ge=1, le=32)
    timeout_minutes: int = Field(default=30, ge=1, le=120)
    keep_temp_files: bool = False
    suffixes: SuffixConfig = Field(default_factory=SuffixConfig)


# ============================================================================
# Word Config
# ============================================================================

class WordConfig(BaseModel):
    """Word document print configuration."""
    orientation: Orientation = Orientation.PORTRAIT
    paper_size: str = "A4"
    margins: MarginType = MarginType.NORMAL
    margins_custom: CustomMargins = Field(default_factory=CustomMargins)
    fit_to_page: bool = True


class WordSettings(BaseModel):
    """Word settings wrapper."""
    default: WordConfig = Field(default_factory=WordConfig)


# ============================================================================
# Excel Config
# ============================================================================

class ExcelPrintConfig(BaseModel):
    """Excel print configuration for a sheet or default."""
    # Scaling
    scaling: ScalingMode = ScalingMode.FIT_COLUMNS
    scaling_percent: int = Field(default=100, ge=1, le=400)
    
    # Page breaks
    rows_per_page: int | None = None
    columns_per_page: int | None = None
    
    # Margins
    margins: MarginType = MarginType.NORMAL
    margins_custom: CustomMargins = Field(default_factory=CustomMargins)
    
    # Header/Footer
    print_header_footer: bool = True
    print_row_col_headings: bool = False
    
    # Mode
    mode: PrintMode = PrintMode.SCREEN_OPTIMIZED
    
    # Paper
    orientation: Orientation = Orientation.LANDSCAPE
    paper_size: str = "A4"


class SheetConfig(BaseModel):
    """Sheet-specific configuration with priority."""
    priority: int = Field(default=99, ge=1)
    names: list[str] | None = None  # None = default for unmatched sheets
    
    # Override settings (optional)
    scaling: ScalingMode | None = None
    scaling_percent: int | None = None
    rows_per_page: int | None = None
    columns_per_page: int | None = None
    margins: MarginType | None = None
    print_header_footer: bool | None = None
    print_row_col_headings: bool | None = None
    mode: PrintMode | None = None
    orientation: Orientation | None = None
    
    def matches_sheet(self, sheet_name: str) -> bool:
        """Check if this config matches a sheet name."""
        if self.names is None:
            return True  # Default config matches all
        
        for pattern in self.names:
            if fnmatch.fnmatch(sheet_name, pattern):
                return True
        return False
    
    def apply_to(self, base: ExcelPrintConfig) -> ExcelPrintConfig:
        """Apply this sheet's overrides to a base config."""
        data = base.model_dump()
        
        for field in [
            "scaling", "scaling_percent", "rows_per_page", "columns_per_page",
            "margins", "print_header_footer", "print_row_col_headings",
            "mode", "orientation"
        ]:
            value = getattr(self, field)
            if value is not None:
                data[field] = value
        
        return ExcelPrintConfig(**data)


class ExcelSettings(BaseModel):
    """Excel settings with default and sheet overrides."""
    default: ExcelPrintConfig = Field(default_factory=ExcelPrintConfig)
    sheets: list[SheetConfig] = Field(default_factory=list)
    
    def get_config_for_sheet(self, sheet_name: str) -> ExcelPrintConfig:
        """Get the configuration for a specific sheet."""
        # Sort by priority (lower = higher priority)
        sorted_sheets = sorted(
            [s for s in self.sheets if s.matches_sheet(sheet_name)],
            key=lambda s: s.priority
        )
        
        if sorted_sheets:
            return sorted_sheets[0].apply_to(self.default)
        
        return self.default


# ============================================================================
# PowerPoint Config
# ============================================================================

class PowerPointConfig(BaseModel):
    """PowerPoint print configuration."""
    slide_size: SlideSize = SlideSize.WIDESCREEN
    output_type: OutputType = OutputType.SLIDES
    handout_layout: int = Field(default=6, ge=1, le=9)
    include_hidden: bool = False
    frame_slides: bool = False
    print_comments: bool = False


class PowerPointSettings(BaseModel):
    """PowerPoint settings wrapper."""
    default: PowerPointConfig = Field(default_factory=PowerPointConfig)


# ============================================================================
# Main Config
# ============================================================================

class ConverterConfig(BaseModel):
    """Root configuration for the document converter."""
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    conversion: ConversionConfig = Field(default_factory=ConversionConfig)
    word: WordSettings = Field(default_factory=WordSettings)
    excel: ExcelSettings = Field(default_factory=ExcelSettings)
    powerpoint: PowerPointSettings = Field(default_factory=PowerPointSettings)
    
    @classmethod
    def load(cls, config_path: Path | None = None) -> "ConverterConfig":
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to config file. If None, uses defaults.
            
        Returns:
            Loaded configuration.
        """
        if config_path is None:
            return cls()
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        return cls.model_validate(data)
    
    def save(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                self.model_dump(mode="json"),
                f,
                default_flow_style=False,
                sort_keys=False,
            )


def get_default_config() -> ConverterConfig:
    """Get default configuration."""
    return ConverterConfig()
