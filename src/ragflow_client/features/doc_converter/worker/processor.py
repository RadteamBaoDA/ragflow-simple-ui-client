"""
Document processor for CPU-bound file processing.

Handles the actual conversion of documents (PDF, DOCX, etc.) to text.
All heavy processing is designed to run via asyncio.to_thread to avoid
blocking the WebSocket heartbeat.
"""

import asyncio
import time
from pathlib import Path
from typing import Callable, Any

from loguru import logger

from ragflow_client.features.doc_converter.schema import (
    ConversionJob,
    JobProgress,
    JobResult,
    JobStatus,
)


# Type alias for progress callback
type ProgressCallback = Callable[[int, str], None]


class DocumentProcessor:
    """
    Processes documents for text extraction and conversion.
    
    This class handles CPU-bound operations and should be run
    via asyncio.to_thread to prevent blocking the event loop.
    
    Example:
        processor = DocumentProcessor()
        result = await processor.process_async(job, progress_callback)
    """
    
    def __init__(self) -> None:
        """Initialize the document processor."""
        self._logger = logger.bind(component="DocumentProcessor")
    
    async def process_async(
        self,
        job: ConversionJob,
        on_progress: ProgressCallback | None = None,
    ) -> JobResult:
        """
        Process a conversion job asynchronously.
        
        Runs the actual processing in a thread pool to avoid
        blocking the WebSocket heartbeat.
        
        Args:
            job: The conversion job to process.
            on_progress: Optional callback for progress updates.
            
        Returns:
            JobResult with the conversion outcome.
        """
        start_time = time.time()
        
        try:
            # Run CPU-bound work in thread pool
            result = await asyncio.to_thread(
                self._process_sync,
                job,
                on_progress,
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            result.duration_ms = duration_ms
            
            return result
            
        except Exception as e:
            self._logger.exception(f"Processing failed for job {job.id}: {e}")
            return JobResult(
                job_id=job.id,
                success=False,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )
    
    def _process_sync(
        self,
        job: ConversionJob,
        on_progress: ProgressCallback | None = None,
    ) -> JobResult:
        """
        Synchronous document processing (runs in thread pool).
        
        Args:
            job: The conversion job to process.
            on_progress: Optional callback for progress updates.
            
        Returns:
            JobResult with the conversion outcome.
        """
        self._logger.info(f"Starting processing for job {job.id}")
        
        # Report initial progress
        if on_progress:
            on_progress(0, "Starting conversion...")
        
        try:
            # Determine source
            if job.source_path:
                source_path = job.source_path
            elif job.source_url:
                # In a real implementation, download the file here
                self._logger.warning(f"URL download not implemented: {job.source_url}")
                if on_progress:
                    on_progress(10, "Downloading file...")
                # Placeholder for download logic
                source_path = None
            else:
                raise ValueError("No source provided")
            
            if source_path is None:
                # Return placeholder result for URL sources
                return JobResult(
                    job_id=job.id,
                    success=True,
                    output_text="[URL download not implemented]",
                    metadata={"source": job.source_url},
                )
            
            if not source_path.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")
            
            # Report progress
            if on_progress:
                on_progress(20, "Reading file...")
            
            # Process based on file extension
            suffix = source_path.suffix.lower()
            
            if suffix in (".txt", ".md", ".rst"):
                result_text = self._process_text_file(source_path, on_progress)
            elif suffix == ".pdf":
                result_text = self._process_pdf_file(source_path, on_progress)
            elif suffix in (".docx", ".doc"):
                result_text = self._process_docx_file(source_path, on_progress)
            else:
                # Try to read as text
                result_text = self._process_text_file(source_path, on_progress)
            
            # Report completion
            if on_progress:
                on_progress(100, "Conversion complete")
            
            return JobResult(
                job_id=job.id,
                success=True,
                output_text=result_text,
                metadata={
                    "source": str(source_path),
                    "size": source_path.stat().st_size,
                    "format": suffix,
                },
            )
            
        except Exception as e:
            self._logger.error(f"Processing error: {e}")
            return JobResult(
                job_id=job.id,
                success=False,
                error=str(e),
            )
    
    def _process_text_file(
        self,
        path: Path,
        on_progress: ProgressCallback | None = None,
    ) -> str:
        """Process a plain text file."""
        if on_progress:
            on_progress(50, "Reading text file...")
        
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try with different encodings
            for encoding in ["latin-1", "cp1252", "iso-8859-1"]:
                try:
                    return path.read_text(encoding=encoding)
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"Could not decode file: {path}")
    
    def _process_pdf_file(
        self,
        path: Path,
        on_progress: ProgressCallback | None = None,
    ) -> str:
        """
        Process a PDF file.
        
        Note: This is a placeholder. In production, you would use
        libraries like PyMuPDF, pdfplumber, or pypdf.
        """
        if on_progress:
            on_progress(50, "Extracting PDF text...")
        
        # Placeholder - in production, use a PDF library
        self._logger.warning("PDF extraction not implemented, returning placeholder")
        return f"[PDF content from: {path.name}]"
    
    def _process_docx_file(
        self,
        path: Path,
        on_progress: ProgressCallback | None = None,
    ) -> str:
        """
        Process a DOCX file.
        
        Note: This is a placeholder. In production, you would use
        python-docx or similar libraries.
        """
        if on_progress:
            on_progress(50, "Extracting DOCX text...")
        
        # Placeholder - in production, use python-docx
        self._logger.warning("DOCX extraction not implemented, returning placeholder")
        return f"[DOCX content from: {path.name}]"
