from pathlib import Path
import pytest
from ragflow_client.features.doc_converter.core.output_manager import OutputManager, FileType
from ragflow_client.features.doc_converter.config.converter_config import SuffixConfig

@pytest.fixture
def suffix_config():
    return SuffixConfig(word="_d", excel="_x", powerpoint="_p")

@pytest.fixture
def output_manager(temp_dir, suffix_config):
    input_dir = temp_dir / "input"
    output_dir = temp_dir / "output"
    input_dir.mkdir()
    return OutputManager(input_dir, output_dir, suffix_config)

def test_get_file_type(output_manager):
    assert output_manager.get_file_type(Path("test.docx")) == FileType.WORD
    assert output_manager.get_file_type(Path("test.xlsx")) == FileType.EXCEL
    assert output_manager.get_file_type(Path("test.pptx")) == FileType.POWERPOINT
    assert output_manager.get_file_type(Path("test.txt")) == FileType.UNKNOWN

def test_get_output_path(output_manager):
    source = output_manager.input_dir / "folder/sub/doc.docx"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("dummy")
    
    output_path = output_manager.get_output_path(source)
    
    expected = output_manager.output_dir / "folder/sub/doc_d.pdf"
    assert output_path == expected
    assert output_path.parent.exists()

def test_record_success_and_summary(output_manager):
    source = Path("doc.docx")
    output_manager.record_success(source)
    output_manager.record_error(source, "failed")
    
    summary = output_manager.get_summary()
    assert summary.total_files == 2
    assert summary.successful == 1
    assert summary.failed == 1
    assert len(summary.errors) == 1
    assert summary.errors[0].error_message == "failed"

def test_cleanup_temp_files(output_manager):
    source = Path("data.xlsm")
    temp_path = output_manager.get_temp_path(source)
    temp_path.write_text("temp")
    
    assert temp_path.exists()
    output_manager.cleanup_temp_files()
    assert not temp_path.exists()
