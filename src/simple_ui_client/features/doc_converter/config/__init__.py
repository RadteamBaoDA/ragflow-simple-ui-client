"""
Configuration Module for Document Converter.

This module contains all configuration-related classes for the converter:
- YAML loading and validation
- Word, Excel, PowerPoint print settings
- Logging and conversion settings

File Structure:
    config/
    ├── __init__.py           (this file)
    └── converter_config.py   (main configuration classes)

Usage:
    from simple_ui_client.features.doc_converter.config import ConverterConfig
    
    config = ConverterConfig.load(Path("config.yaml"))
    print(config.word.default.orientation)

Author: Simple UI Team
"""

from simple_ui_client.features.doc_converter.config.converter_config import (
    # Enums
    LogLevel,
    Orientation,
    MarginType,
    ScalingMode,
    PrintMode,
    SlideSize,
    OutputType,
    # Config classes
    CustomMargins,
    LoggingConfig,
    SuffixConfig,
    ConversionConfig,
    WordConfig,
    WordSettings,
    ExcelPrintConfig,
    SheetConfig,
    ExcelSettings,
    PowerPointConfig,
    PowerPointSettings,
    ConverterConfig,
    # Functions
    get_default_config,
)

__all__ = [
    # Enums
    "LogLevel",
    "Orientation",
    "MarginType",
    "ScalingMode",
    "PrintMode",
    "SlideSize",
    "OutputType",
    # Config classes
    "CustomMargins",
    "LoggingConfig",
    "SuffixConfig",
    "ConversionConfig",
    "WordConfig",
    "WordSettings",
    "ExcelPrintConfig",
    "SheetConfig",
    "ExcelSettings",
    "PowerPointConfig",
    "PowerPointSettings",
    "ConverterConfig",
    # Functions
    "get_default_config",
]
