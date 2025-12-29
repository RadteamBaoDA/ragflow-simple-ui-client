"""
Temporary file management service.

Provides async file operations with proper cleanup and cross-platform path handling.
Uses pathlib.Path for all path operations.
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from loguru import logger

if TYPE_CHECKING:
    from simple_ui_client.utils.config import Settings


class FileManager:
    """
    Manages temporary files and directories for document processing.
    
    Features:
    - Async file operations (read, write, copy)
    - Automatic cleanup with context managers
    - Cross-platform path handling with pathlib
    - Unique temp directory per session
    """
    
    def __init__(self, settings: "Settings" | None = None) -> None:
        """
        Initialize the file manager.
        
        Args:
            settings: Optional settings for custom temp directory location.
        """
        self.settings = settings
        self._temp_base: Path | None = None
        self._logger = logger.bind(component="FileManager")
    
    @property
    def temp_base(self) -> Path:
        """Get or create the base temporary directory."""
        if self._temp_base is None or not self._temp_base.exists():
            self._temp_base = Path(tempfile.mkdtemp(prefix="simple_ui_"))
            self._logger.debug(f"Created temp base: {self._temp_base}")
        return self._temp_base
    
    def create_temp_dir(self, prefix: str = "job_") -> Path:
        """
        Create a new temporary directory.
        
        Args:
            prefix: Prefix for the directory name.
            
        Returns:
            Path to the created directory.
        """
        temp_dir = self.temp_base / f"{prefix}{uuid4().hex[:8]}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        self._logger.debug(f"Created temp dir: {temp_dir}")
        return temp_dir
    
    def create_temp_file(self, suffix: str = "", prefix: str = "file_") -> Path:
        """
        Create a new temporary file path (doesn't create the file).
        
        Args:
            suffix: File extension/suffix.
            prefix: Prefix for the filename.
            
        Returns:
            Path to the temp file location.
        """
        filename = f"{prefix}{uuid4().hex[:8]}{suffix}"
        return self.temp_base / filename
    
    async def read_file(self, path: Path) -> bytes:
        """
        Read file contents asynchronously.
        
        Args:
            path: Path to the file to read.
            
        Returns:
            File contents as bytes.
        """
        return await asyncio.to_thread(path.read_bytes)
    
    async def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        """
        Read file contents as text asynchronously.
        
        Args:
            path: Path to the file to read.
            encoding: Text encoding.
            
        Returns:
            File contents as string.
        """
        return await asyncio.to_thread(path.read_text, encoding)
    
    async def write_file(self, path: Path, content: bytes) -> None:
        """
        Write content to file asynchronously.
        
        Args:
            path: Path to the file to write.
            content: Bytes to write.
        """
        await asyncio.to_thread(path.write_bytes, content)
        self._logger.debug(f"Wrote {len(content)} bytes to {path}")
    
    async def write_text(self, path: Path, content: str, encoding: str = "utf-8") -> None:
        """
        Write text content to file asynchronously.
        
        Args:
            path: Path to the file to write.
            content: Text to write.
            encoding: Text encoding.
        """
        await asyncio.to_thread(path.write_text, content, encoding)
        self._logger.debug(f"Wrote {len(content)} chars to {path}")
    
    async def copy_file(self, src: Path, dst: Path) -> Path:
        """
        Copy a file asynchronously.
        
        Args:
            src: Source file path.
            dst: Destination file path.
            
        Returns:
            Path to the copied file.
        """
        result = await asyncio.to_thread(shutil.copy2, src, dst)
        self._logger.debug(f"Copied {src} -> {dst}")
        return Path(result)
    
    async def delete_file(self, path: Path) -> bool:
        """
        Delete a file asynchronously.
        
        Args:
            path: Path to the file to delete.
            
        Returns:
            True if file was deleted, False if it didn't exist.
        """
        try:
            await asyncio.to_thread(path.unlink, missing_ok=True)
            self._logger.debug(f"Deleted file: {path}")
            return True
        except Exception as e:
            self._logger.warning(f"Failed to delete {path}: {e}")
            return False
    
    async def delete_dir(self, path: Path) -> bool:
        """
        Delete a directory and its contents asynchronously.
        
        Args:
            path: Path to the directory to delete.
            
        Returns:
            True if directory was deleted, False otherwise.
        """
        try:
            await asyncio.to_thread(shutil.rmtree, path, ignore_errors=True)
            self._logger.debug(f"Deleted dir: {path}")
            return True
        except Exception as e:
            self._logger.warning(f"Failed to delete dir {path}: {e}")
            return False
    
    @asynccontextmanager
    async def temp_directory(self, prefix: str = "job_") -> AsyncIterator[Path]:
        """
        Context manager for a temporary directory that's cleaned up on exit.
        
        Args:
            prefix: Prefix for the directory name.
            
        Yields:
            Path to the temporary directory.
        """
        temp_dir = self.create_temp_dir(prefix)
        try:
            yield temp_dir
        finally:
            await self.delete_dir(temp_dir)
    
    @asynccontextmanager
    async def temp_file(self, suffix: str = "", prefix: str = "file_") -> AsyncIterator[Path]:
        """
        Context manager for a temporary file that's cleaned up on exit.
        
        Args:
            suffix: File extension/suffix.
            prefix: Prefix for the filename.
            
        Yields:
            Path to the temporary file.
        """
        temp_path = self.create_temp_file(suffix, prefix)
        try:
            yield temp_path
        finally:
            await self.delete_file(temp_path)
    
    async def cleanup(self) -> None:
        """Clean up all temporary files and directories."""
        if self._temp_base and self._temp_base.exists():
            await self.delete_dir(self._temp_base)
            self._temp_base = None
            self._logger.info("Cleaned up all temp files")
    
    def file_exists(self, path: Path) -> bool:
        """Check if a file exists."""
        return path.exists() and path.is_file()
    
    def dir_exists(self, path: Path) -> bool:
        """Check if a directory exists."""
        return path.exists() and path.is_dir()
