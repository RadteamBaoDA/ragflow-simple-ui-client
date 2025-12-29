import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from simple_ui_client.features.doc_converter.engine.linux.converter import LinuxConverter

@pytest.fixture
def converter():
    # Patch the sub-converters to avoid actual initialization/dependencies
    with patch("simple_ui_client.features.doc_converter.engine.linux.converter.LinuxWordConverter"), \
         patch("simple_ui_client.features.doc_converter.engine.linux.converter.LinuxExcelConverter"), \
         patch("simple_ui_client.features.doc_converter.engine.linux.converter.LinuxPowerPointConverter"):
        return LinuxConverter(libreoffice_path="test-office")

def test_linux_converter_init(converter):
    assert converter._libreoffice_path == "test-office"
    assert converter._word_converter is not None
    assert converter._excel_converter is not None
    assert converter._powerpoint_converter is not None

def test_linux_converter_initialize(converter):
    # Should be a no-op but safe to call
    converter.initialize()
    # No exception raised is success

def test_linux_converter_cleanup(converter):
    # Should be a no-op but safe to call
    converter.cleanup()
    # No exception raised is success

def test_linux_converter_delegation(converter):
    source = Path("test.docx")
    target = Path("test.pdf")
    config = MagicMock()
    
    # Test Word
    converter.convert_word(source, target, config)
    converter._word_converter.convert.assert_called_once_with(source, target, config)
    
    # Test Excel
    converter.convert_excel(source, target, config, "Sheet1")
    converter._excel_converter.convert.assert_called_once_with(source, target, config, "Sheet1")
    
    # Test PowerPoint
    converter.convert_powerpoint(source, target, config)
    converter._powerpoint_converter.convert.assert_called_once_with(source, target, config)
    
    # Test XLSM to XLSX
    converter.convert_xlsm_to_xlsx(source, target)
    converter._excel_converter.convert_xlsm_to_xlsx.assert_called_once_with(source, target)

def test_linux_converter_properties(converter):
    assert converter.supports_parallel is True
    assert "Linux" in converter.name
