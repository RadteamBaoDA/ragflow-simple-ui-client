"""
Prerequisite checker for document conversion.

Verifies that Office 365 (Windows) or LibreOffice (Linux) is installed
before attempting document conversions.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from loguru import logger


class PrerequisiteError(Exception):
    """Raised when required software is not installed."""
    pass


@dataclass
class PrerequisiteStatus:
    """Status of prerequisite checks."""
    is_installed: bool
    application: str
    version: str | None = None
    path: str | None = None
    message: str = ""


def check_windows_office() -> PrerequisiteStatus:
    """
    Check if Microsoft Office is installed on Windows.
    
    Returns:
        PrerequisiteStatus with Office installation details.
    """
    try:
        import winreg
        
        # Check common Office registry paths
        office_paths = [
            r"SOFTWARE\Microsoft\Office\ClickToRun\Configuration",
            r"SOFTWARE\Microsoft\Office\16.0\Common\InstallRoot",
            r"SOFTWARE\Microsoft\Office\15.0\Common\InstallRoot",
        ]
        
        for reg_path in office_paths:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                winreg.CloseKey(key)
                
                return PrerequisiteStatus(
                    is_installed=True,
                    application="Microsoft Office",
                    message="Microsoft Office is installed",
                )
            except FileNotFoundError:
                continue
        
        # Try to instantiate COM objects as fallback
        try:
            import win32com.client
            word = win32com.client.Dispatch("Word.Application")
            version = word.Version
            word.Quit()
            
            return PrerequisiteStatus(
                is_installed=True,
                application="Microsoft Office",
                version=version,
                message=f"Microsoft Office {version} is installed",
            )
        except Exception:
            pass
        
        return PrerequisiteStatus(
            is_installed=False,
            application="Microsoft Office",
            message=(
                "Microsoft Office is not installed. "
                "Please install Microsoft Office 365 or Microsoft Office 2016+ "
                "to use the document converter on Windows."
            ),
        )
        
    except ImportError:
        return PrerequisiteStatus(
            is_installed=False,
            application="Microsoft Office",
            message=(
                "pywin32 is not installed. "
                "Please install it with: pip install pywin32"
            ),
        )


def check_linux_libreoffice() -> PrerequisiteStatus:
    """
    Check if LibreOffice is installed on Linux.
    
    Returns:
        PrerequisiteStatus with LibreOffice installation details.
    """
    # Check if libreoffice is in PATH
    libreoffice_path = shutil.which("libreoffice")
    
    if libreoffice_path is None:
        # Try common installation paths
        common_paths = [
            "/usr/bin/libreoffice",
            "/usr/local/bin/libreoffice",
            "/snap/bin/libreoffice",
            "/opt/libreoffice/program/soffice",
        ]
        
        for path in common_paths:
            if Path(path).exists():
                libreoffice_path = path
                break
    
    if libreoffice_path is None:
        return PrerequisiteStatus(
            is_installed=False,
            application="LibreOffice",
            message=(
                "LibreOffice is not installed. "
                "Please install it with:\n"
                "  Ubuntu/Debian: sudo apt install libreoffice\n"
                "  Fedora: sudo dnf install libreoffice\n"
                "  Arch: sudo pacman -S libreoffice-fresh"
            ),
        )
    
    # Get version
    try:
        result = subprocess.run(
            [libreoffice_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version = result.stdout.strip().split("\n")[0] if result.stdout else None
        
        return PrerequisiteStatus(
            is_installed=True,
            application="LibreOffice",
            version=version,
            path=libreoffice_path,
            message=f"LibreOffice is installed: {version}",
        )
    except Exception as e:
        logger.warning(f"Could not get LibreOffice version: {e}")
        return PrerequisiteStatus(
            is_installed=True,
            application="LibreOffice",
            path=libreoffice_path,
            message="LibreOffice is installed",
        )


def check_prerequisites() -> PrerequisiteStatus:
    """
    Check if required software is installed for the current platform.
    
    Returns:
        PrerequisiteStatus with installation details.
        
    Raises:
        PrerequisiteError: If required software is not installed.
    """
    if sys.platform == "win32":
        status = check_windows_office()
    else:
        status = check_linux_libreoffice()
    
    if not status.is_installed:
        raise PrerequisiteError(status.message)
    
    logger.info(status.message)
    return status


def check_prerequisites_silent() -> PrerequisiteStatus:
    """
    Check prerequisites without raising an exception.
    
    Returns:
        PrerequisiteStatus indicating whether software is installed.
    """
    if sys.platform == "win32":
        return check_windows_office()
    else:
        return check_linux_libreoffice()
