import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

mock_win32com_client = MagicMock()

@pytest.fixture(autouse=True)
def mock_win32_env():
    with patch.dict(sys.modules, {
        "pythoncom": MagicMock(),
        "win32com": MagicMock(),
        "win32com.client": mock_win32com_client,
    }):
        yield
    mock_win32com_client.reset_mock()

@pytest.fixture
def converter():
    if "ragflow_client.features.doc_converter.engine.windows.powerpoint" in sys.modules:
        del sys.modules["ragflow_client.features.doc_converter.engine.windows.powerpoint"]
    from ragflow_client.features.doc_converter.engine.windows.powerpoint import WindowsPowerPointConverter
    return WindowsPowerPointConverter()

def test_windows_powerpoint_convert_success(converter):
    source = Path("test.pptx")
    target = Path("test.pdf")
    config = MagicMock()
    config.output_type = "slides"
    config.include_hidden = False
    
    # Mock COM
    mock_ppt = MagicMock()
    mock_pres = MagicMock()
    
    mock_win32com_client.Dispatch.return_value = mock_ppt
    mock_ppt.Presentations.Open.return_value = mock_pres
    mock_pres.Slides.Count = 12
    
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.absolute", return_value=Path("/abs/test.pptx")):
        
        result = converter.convert(source, target, config)
        
        assert result.success is True
        assert result.pages == 12
        mock_ppt.Quit.assert_called_once()
        mock_pres.SaveAs.assert_called_once()
