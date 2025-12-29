import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import subprocess
from ragflow_client.features.doc_converter.engine.linux.word import LinuxWordConverter

@pytest.fixture
def converter():
    return LinuxWordConverter(libreoffice_path="libreoffice")

def test_linux_word_convert_success(converter):
    source = Path("test.docx")
    target = Path("test.pdf")
    config = MagicMock()
    
    with patch("subprocess.run") as mock_run, \
         patch("pathlib.Path.mkdir") as mock_mkdir, \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.rename") as mock_rename:
        
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        result = converter.convert(source, target, config)
        
        assert result.success is True
        assert result.source_path == source
        assert result.output_path == target
        mock_run.assert_called_once()
        assert "--convert-to" in mock_run.call_args[0][0]
        assert "pdf" in mock_run.call_args[0][0]

def test_linux_word_convert_failure(converter):
    source = Path("test.docx")
    target = Path("test.pdf")
    config = MagicMock()
    
    with patch("subprocess.run") as mock_run, \
         patch("pathlib.Path.mkdir"):
        
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error message")
        
        result = converter.convert(source, target, config)
        
        assert result.success is False
        assert "Error message" in result.error

def test_linux_word_convert_timeout(converter):
    source = Path("test.docx")
    target = Path("test.pdf")
    config = MagicMock()
    
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="test", timeout=300)), \
         patch("pathlib.Path.mkdir"):
        
        result = converter.convert(source, target, config)
        
        assert result.success is False
        assert "timed out" in result.error
