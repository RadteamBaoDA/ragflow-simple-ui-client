import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from simple_ui_client.features.doc_converter.engine.linux.excel import LinuxExcelConverter

@pytest.fixture
def converter():
    return LinuxExcelConverter()

def test_linux_excel_convert_success(converter):
    source = Path("test.xlsx")
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

def test_linux_excel_convert_xlsm(converter):
    source = Path("test.xlsm")
    target = Path("test.xlsx")
    
    with patch("subprocess.run") as mock_run, \
         patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.rename"):
        
        mock_run.return_value = MagicMock(returncode=0)
        
        result = converter.convert_xlsm_to_xlsx(source, target)
        assert result.success is True
        assert "--convert-to" in mock_run.call_args[0][0]
        assert "xlsx" in mock_run.call_args[0][0]
