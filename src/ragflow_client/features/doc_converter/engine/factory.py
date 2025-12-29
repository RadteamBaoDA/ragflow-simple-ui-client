"""
Converter factory for platform-specific engine selection.

This module automatically selects the appropriate converter based on
the current operating system (Windows vs Linux/macOS).

Design Pattern: Factory Pattern
    - The factory creates the correct converter type
    - Callers don't need to know which converter to use
    - Easy to add new platforms in the future

Author: RAGFlow Team
Created: December 2024
"""

from __future__ import annotations

import sys  # Used to detect the operating system
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from ragflow_client.features.doc_converter.engine.base import BaseConverter


def get_converter() -> "BaseConverter":
    """
    Get the appropriate converter for the current platform.
    
    This factory function:
    1. Checks the operating system
    2. Creates the correct converter instance
    3. Returns it with a consistent interface
    
    Platform detection:
        - Windows (win32): Uses Microsoft Office 365 via COM
        - Linux (linux, linux2): Uses LibreOffice headless
        - macOS (darwin): Uses LibreOffice headless
    
    Returns:
        BaseConverter: A converter instance for the current platform.
                      Call initialize() before use and cleanup() when done.
    
    Raises:
        RuntimeError: If no converter is available for the platform.
    
    Example:
        converter = get_converter()
        print(f"Using: {converter.name}")
        
        converter.initialize()
        try:
            result = converter.convert_word(source, target, config)
        finally:
            converter.cleanup()
    """
    # sys.platform returns a string identifying the OS:
    #   'win32' - Windows (even on 64-bit)
    #   'linux' or 'linux2' - Linux
    #   'darwin' - macOS
    
    if sys.platform == "win32":
        # Windows: Use Office 365 COM automation
        # Provides highest fidelity conversion with full Office features
        from ragflow_client.features.doc_converter.engine.windows import WindowsConverter
        logger.info("Using Windows Office 365 COM converter")
        return WindowsConverter()
    
    elif sys.platform in ("linux", "linux2", "darwin"):
        # Linux/macOS: Use LibreOffice in headless mode
        # Good compatibility with Office formats via open-source tools
        from ragflow_client.features.doc_converter.engine.linux import LinuxConverter
        logger.info("Using LibreOffice converter for Linux/macOS")
        return LinuxConverter()
    
    else:
        # Unknown platform - no converter available
        raise RuntimeError(
            f"No converter available for platform: {sys.platform}. "
            f"Supported platforms: Windows (win32), Linux, macOS (darwin)"
        )


def get_converter_info() -> dict[str, str]:
    """
    Get information about the converter that would be used.
    
    Useful for displaying to users or logging before conversion.
    Does not create a converter instance.
    
    Returns:
        Dictionary containing:
            - platform: OS name
            - converter: Converter technology used
            - requirements: What needs to be installed
    
    Example:
        info = get_converter_info()
        print(f"Platform: {info['platform']}")
        print(f"Requirements: {info['requirements']}")
    """
    if sys.platform == "win32":
        return {
            "platform": "Windows",
            "converter": "Microsoft Office 365 COM",
            "requirements": "Microsoft Office 365 or Office 2016+",
        }
    elif sys.platform in ("linux", "linux2"):
        return {
            "platform": "Linux",
            "converter": "LibreOffice",
            "requirements": "LibreOffice (apt install libreoffice)",
        }
    elif sys.platform == "darwin":
        return {
            "platform": "macOS",
            "converter": "LibreOffice",
            "requirements": "LibreOffice (brew install libreoffice)",
        }
    else:
        return {
            "platform": sys.platform,
            "converter": "Unknown",
            "requirements": "Platform not supported",
        }
