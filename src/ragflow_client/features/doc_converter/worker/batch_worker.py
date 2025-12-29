"""
Batch worker for parallel document conversion.

Manages a worker pool for processing multiple documents with
parallel or sequential fallback support.
"""

from __future__ import annotations

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from loguru import logger

from ragflow_client.features.doc_converter.engine.base import ConversionResult
from ragflow_client.features.doc_converter.engine.factory import get_converter
from ragflow_client.features.doc_converter.core.output_manager import (
    FileType,
    OutputManager,
    discover_files,
)

if TYPE_CHECKING:
    from ragflow_client.features.doc_converter.config.converter_config import ConverterConfig
    from ragflow_client.features.doc_converter.engine.base import BaseConverter
    from ragflow_client.features.doc_converter.ui.progress_ui import ProgressManager


@dataclass
class BatchResult:
    """Result of a batch conversion."""
    total_files: int
    successful: int
    failed: int
    duration_seconds: float
    summary_path: Path | None = None


class BatchWorker:
    """
    Worker for batch document conversion.
    
    Supports parallel processing with automatic fallback to
    sequential if parallel is not supported or fails.
    
    Example:
        worker = BatchWorker(config, progress_manager)
        result = await worker.process_batch(files, output_manager)
    """
    
    def __init__(
        self,
        config: "ConverterConfig",
        progress: "ProgressManager | None" = None,
    ) -> None:
        """
        Initialize the batch worker.
        
        Args:
            config: Converter configuration.
            progress: Optional progress manager for UI updates.
        """
        self.config = config
        self.progress = progress
        self._logger = logger.bind(component="BatchWorker")
        self._parallel_failures = 0
        self._max_parallel_failures = 3
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Log a message and update progress UI."""
        getattr(self._logger, level.lower())(message)
        if self.progress:
            self.progress.add_log(message, level, threading.current_thread().name)
    
    def _convert_file(
        self,
        converter: "BaseConverter",
        source: Path,
        output_manager: OutputManager,
    ) -> ConversionResult:
        """
        Convert a single file.
        
        Args:
            converter: The converter to use.
            source: Source file path.
            output_manager: Output manager instance.
            
        Returns:
            ConversionResult from the conversion.
        """
        # Initialize COM for this thread (Windows)
        converter.initialize()
        
        try:
            file_type = output_manager.get_file_type(source)
            target = output_manager.get_output_path(source)
            
            self._log(f"Converting: {source.name}")
            
            if self.progress:
                self.progress.start_file(source.name)
            
            # Handle macro Excel files
            if output_manager.is_macro_excel(source):
                temp_path = output_manager.get_temp_path(source, ".xlsx")
                result = converter.convert_xlsm_to_xlsx(source, temp_path)
                
                if not result.success:
                    return result
                
                source = temp_path
            
            # Convert based on file type
            if file_type == FileType.WORD:
                result = converter.convert_word(
                    source, target, self.config.word.default
                )
            elif file_type == FileType.EXCEL:
                result = converter.convert_excel(
                    source, target, self.config.excel.default
                )
            elif file_type == FileType.POWERPOINT:
                result = converter.convert_powerpoint(
                    source, target, self.config.powerpoint.default
                )
            else:
                result = ConversionResult(
                    success=False,
                    source_path=source,
                    error=f"Unsupported file type: {source.suffix}",
                )
            
            if self.progress:
                self.progress.complete_file(
                    source.name,
                    success=result.success,
                    error=result.error,
                )
            
            return result
            
        finally:
            converter.cleanup()
    
    def _process_file_with_timeout(
        self,
        converter: "BaseConverter",
        source: Path,
        output_manager: OutputManager,
        timeout_seconds: int,
    ) -> ConversionResult:
        """Process a file with timeout handling."""
        start_time = time.time()
        
        try:
            result = self._convert_file(converter, source, output_manager)
            return result
            
        except Exception as e:
            self._log(f"Error converting {source.name}: {e}", "ERROR")
            return ConversionResult(
                success=False,
                source_path=source,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )
    
    async def process_batch(
        self,
        files: list[Path],
        output_manager: OutputManager,
    ) -> BatchResult:
        """
        Process a batch of files.
        
        Args:
            files: List of files to convert.
            output_manager: Output manager instance.
            
        Returns:
            BatchResult with conversion statistics.
        """
        start_time = time.time()
        
        if not files:
            self._log("No files to process", "WARNING")
            return BatchResult(
                total_files=0,
                successful=0,
                failed=0,
                duration_seconds=0,
            )
        
        self._log(f"Starting batch conversion of {len(files)} files")
        
        converter = get_converter()
        timeout_seconds = self.config.conversion.timeout_minutes * 60
        workers = self.config.conversion.workers
        
        # Check if parallel is supported
        use_parallel = converter.supports_parallel and workers > 1
        
        if use_parallel:
            self._log(f"Using parallel processing with {workers} workers")
            result = await self._process_parallel(
                files, output_manager, converter, workers, timeout_seconds
            )
        else:
            self._log("Using sequential processing")
            result = await self._process_sequential(
                files, output_manager, converter, timeout_seconds
            )
        
        # Check if we need to fallback to sequential
        if use_parallel and self._parallel_failures >= self._max_parallel_failures:
            self._log(
                f"Too many parallel failures ({self._parallel_failures}), "
                "switching to sequential",
                "WARNING"
            )
            # Reprocess failed files sequentially
            failed_files = [
                f for f in files
                if not (output_manager.get_output_path(f)).exists()
            ]
            if failed_files:
                self._log(f"Reprocessing {len(failed_files)} failed files sequentially")
                await self._process_sequential(
                    failed_files, output_manager, converter, timeout_seconds
                )
        
        # Generate summary report
        summary_path = output_manager.generate_summary_report()
        
        # Cleanup temp files
        output_manager.cleanup_temp_files()
        
        duration = time.time() - start_time
        summary = output_manager.get_summary()
        
        self._log(
            f"Batch complete: {summary.successful}/{summary.total_files} successful "
            f"in {duration:.1f}s"
        )
        
        return BatchResult(
            total_files=summary.total_files,
            successful=summary.successful,
            failed=summary.failed,
            duration_seconds=duration,
            summary_path=summary_path,
        )
    
    async def _process_parallel(
        self,
        files: list[Path],
        output_manager: OutputManager,
        converter: "BaseConverter",
        workers: int,
        timeout_seconds: int,
    ) -> BatchResult:
        """Process files in parallel using thread pool."""
        
        def process_one(source: Path) -> ConversionResult:
            # Create new converter instance for this thread
            thread_converter = get_converter()
            return self._process_file_with_timeout(
                thread_converter, source, output_manager, timeout_seconds
            )
        
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures: dict[Future[ConversionResult], Path] = {}
            
            for source in files:
                future = executor.submit(process_one, source)
                futures[future] = source
            
            for future in as_completed(futures, timeout=timeout_seconds * len(files)):
                source = futures[future]
                try:
                    result = future.result(timeout=timeout_seconds)
                    
                    if result.success:
                        output_manager.record_success(source)
                    else:
                        output_manager.record_error(source, result.error or "Unknown error")
                        self._parallel_failures += 1
                        
                except Exception as e:
                    self._log(f"Parallel task failed for {source.name}: {e}", "ERROR")
                    output_manager.record_error(source, str(e))
                    self._parallel_failures += 1
        
        summary = output_manager.get_summary()
        return BatchResult(
            total_files=summary.total_files,
            successful=summary.successful,
            failed=summary.failed,
            duration_seconds=(summary.end_time - summary.start_time).total_seconds()
            if summary.end_time else 0,
        )
    
    async def _process_sequential(
        self,
        files: list[Path],
        output_manager: OutputManager,
        converter: "BaseConverter",
        timeout_seconds: int,
    ) -> BatchResult:
        """Process files sequentially."""
        
        for source in files:
            try:
                result = await asyncio.to_thread(
                    self._process_file_with_timeout,
                    converter,
                    source,
                    output_manager,
                    timeout_seconds,
                )
                
                if result.success:
                    output_manager.record_success(source)
                else:
                    output_manager.record_error(source, result.error or "Unknown error")
                    
            except asyncio.TimeoutError:
                self._log(f"Timeout converting {source.name}", "ERROR")
                output_manager.record_error(source, f"Timeout after {timeout_seconds}s")
                
            except Exception as e:
                self._log(f"Error converting {source.name}: {e}", "ERROR")
                output_manager.record_error(source, str(e))
        
        summary = output_manager.get_summary()
        return BatchResult(
            total_files=summary.total_files,
            successful=summary.successful,
            failed=summary.failed,
            duration_seconds=(summary.end_time - summary.start_time).total_seconds()
            if summary.end_time else 0,
        )
