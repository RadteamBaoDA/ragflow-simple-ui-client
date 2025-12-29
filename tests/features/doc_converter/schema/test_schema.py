from pathlib import Path
import pytest
from uuid import UUID
from ragflow_client.features.doc_converter.schema.schema import ConversionJob, JobStatus, JobProgress

def test_conversion_job_validation():
    # Valid with path
    job = ConversionJob(source_path="test.docx")
    assert isinstance(job.id, UUID)
    assert isinstance(job.source_path, Path)
    
    # Valid with URL
    job = ConversionJob(source_url="http://example.com/doc.docx")
    assert job.source_url == "http://example.com/doc.docx"
    
    # Invalid (missing both)
    with pytest.raises(ValueError, match="Either source_url or source_path must be provided"):
        ConversionJob()

def test_job_progress():
    job = ConversionJob(source_path="test.docx")
    progress = JobProgress(job_id=job.id, progress=50, message="Processing...")
    
    assert progress.job_id == job.id
    assert progress.progress == 50
    assert progress.status == JobStatus.PROCESSING

def test_job_status_enum():
    assert JobStatus.COMPLETED == "completed"
    assert JobStatus.FAILED == "failed"
