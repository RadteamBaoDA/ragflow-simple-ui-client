"""
Pydantic models for document conversion jobs.

Defines the data structures for job requests, progress updates, and results.
All internal events use these models for payload validation.
"""

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class JobStatus(str, Enum):
    """Status of a conversion job."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConversionJob(BaseModel):
    """
    Document conversion job request.
    
    Attributes:
        id: Unique job identifier.
        source_url: URL to download the source document.
        source_path: Local path to the source document (alternative to URL).
        target_format: Desired output format.
        options: Additional conversion options.
        created_at: When the job was created.
        priority: Job priority (higher = more urgent).
    """
    
    id: UUID = Field(default_factory=uuid4)
    source_url: str | None = None
    source_path: Path | None = None
    target_format: str = "text"
    options: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    priority: int = Field(default=0, ge=0, le=10)
    
    @field_validator("source_path", mode="before")
    @classmethod
    def convert_path(cls, v: str | Path | None) -> Path | None:
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v
    
    def model_post_init(self, __context: Any) -> None:
        """Validate that at least one source is provided."""
        if not self.source_url and not self.source_path:
            raise ValueError("Either source_url or source_path must be provided")


class JobProgress(BaseModel):
    """
    Progress update for a conversion job.
    
    Attributes:
        job_id: The job this progress belongs to.
        progress: Progress percentage (0-100).
        status: Current job status.
        message: Optional status message.
        updated_at: When this update was created.
    """
    
    job_id: UUID
    progress: int = Field(ge=0, le=100)
    status: JobStatus = JobStatus.PROCESSING
    message: str = ""
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JobResult(BaseModel):
    """
    Result of a conversion job.
    
    Attributes:
        job_id: The job this result belongs to.
        success: Whether the conversion succeeded.
        output_path: Path to the converted file (if successful).
        output_text: Extracted text content (if applicable).
        error: Error message (if failed).
        metadata: Additional metadata about the conversion.
        completed_at: When the job completed.
        duration_ms: Processing duration in milliseconds.
    """
    
    job_id: UUID
    success: bool
    output_path: Path | None = None
    output_text: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: int = 0
    
    @field_validator("output_path", mode="before")
    @classmethod
    def convert_output_path(cls, v: str | Path | None) -> Path | None:
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v
