import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from ragflow_client.features.doc_converter.engine.windows.converter import WindowsConverter

@pytest.fixture
def converter():
    with patch("ragflow_client.features.doc_converter.engine.windows.converter.WindowsWordConverter"), \
         patch("ragflow_client.features.doc_converter.engine.windows.converter.WindowsExcelConverter"), \
         patch("ragflow_client.features.doc_converter.engine.windows.converter.WindowsPowerPointConverter"):
        return WindowsConverter()

def test_windows_converter_initialize(converter):
    converter.initialize()
    assert converter._initialized is True
    converter._word_converter.initialize.assert_called_once()
    converter._excel_converter.initialize.assert_called_once()
    converter._powerpoint_converter.initialize.assert_called_once()

def test_windows_converter_delegation(converter):
    source = Path("test.docx")
    target = Path("test.pdf")
    config = MagicMock()
    
    converter.convert_word(source, target, config)
    converter._word_converter.convert.assert_called_once_with(source, target, config)
    
    converter.convert_excel(source, target, config, "Sheet1")
    converter._excel_converter.convert.assert_called_once_with(source, target, config, "Sheet1")
    
    converter.convert_powerpoint(source, target, config)
    converter._powerpoint_converter.convert.assert_called_once_with(source, target, config)

def test_windows_converter_properties(converter):
    assert converter.supports_parallel is True
    assert "Windows" in converter.name
