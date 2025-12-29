import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from ragflow_client.features.doc_converter.engine.linux.powerpoint import LinuxPowerPointConverter

@pytest.fixture
def converter():
    return LinuxPowerPointConverter()

def test_linux_powerpoint_convert_success(converter):
    source = Path("test.pptx")
    target = Path("test.pdf")
    config = MagicMock()
    
    with patch("subprocess.run") as mock_run, \
         patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.rename"):
        
        mock_run.return_value = MagicMock(returncode=0)
        
        result = converter.convert(source, target, config)
        assert result.success is True
        mock_run.assert_called_once()
