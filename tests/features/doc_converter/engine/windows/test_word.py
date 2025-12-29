import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# We MUST mock win32 dependencies BEFORE the class is even used
@pytest.fixture(autouse=True)
def mock_win32():
    # Helper to create a mock module structure
    mock_client = MagicMock()
    mock_pythoncom = MagicMock()
    
    with patch.dict(sys.modules, {
        "win32com": MagicMock(),
        "win32com.client": mock_client,
        "pythoncom": mock_pythoncom
    }):
        yield mock_client

@pytest.fixture
def converter():
    # Import inside fixture to ensure it uses the mocks
    from simple_ui_client.features.doc_converter.engine.windows.word import WindowsWordConverter
    return WindowsWordConverter()

def test_windows_word_convert_success(converter, mock_win32):
    from simple_ui_client.features.doc_converter.config import Orientation, MarginType
    
    source = Path("test.docx")
    target = Path("test.pdf")
    config = MagicMock()
    config.orientation = Orientation.PORTRAIT
    config.margins = MarginType.NORMAL
    
    # Setup COM chain
    mock_word = MagicMock()
    mock_doc = MagicMock()
    
    # Dispatch("Word.Application") -> mock_word
    mock_win32.Dispatch.return_value = mock_word
    # word.Documents.Open(...) -> mock_doc
    mock_word.Documents.Open.return_value = mock_doc
    # doc.ComputeStatistics(2) -> 5
    mock_doc.ComputeStatistics.return_value = 5
    
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.absolute", return_value=Path("/abs/test.docx")):
        
        result = converter.convert(source, target, config)
        
        assert result.success is True
        assert result.pages == 5
        mock_word.Quit.assert_called_once()

def test_windows_word_convert_failure(converter, mock_win32):
    source = Path("test.docx")
    target = Path("test.pdf")
    config = MagicMock()
    
    # Simulate COM error
    mock_win32.Dispatch.side_effect = Exception("COM Error")
    
    result = converter.convert(source, target, config)
    assert result.success is False
    assert "COM Error" in result.error
