import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

mock_win32com_client = MagicMock()

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
    if "simple_ui_client.features.doc_converter.engine.windows.excel" in sys.modules:
        del sys.modules["simple_ui_client.features.doc_converter.engine.windows.excel"]
    from simple_ui_client.features.doc_converter.engine.windows.excel import WindowsExcelConverter
    return WindowsExcelConverter()

def test_windows_excel_convert_success(converter):
    from simple_ui_client.features.doc_converter.config import Orientation, MarginType, ScalingMode
    
    source = Path("test.xlsx")
    target = Path("test.pdf")
    config = MagicMock()
    config.orientation = Orientation.LANDSCAPE
    config.margins = MarginType.NARROW
    config.scaling = ScalingMode.FIT_SHEET
    config.print_header_footer = True
    config.print_row_col_headings = False
    config.rows_per_page = None
    config.columns_per_page = None
    
    # Mock COM
    mock_excel = MagicMock()
    mock_wb = MagicMock()
    mock_sheet = MagicMock()
    
    mock_win32com_client.Dispatch.return_value = mock_excel
    mock_excel.Workbooks.Open.return_value = mock_wb
    mock_wb.Worksheets = [mock_sheet]
    
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.absolute", return_value=Path("/abs/test.xlsx")):
        
        result = converter.convert(source, target, config)
        
        assert result.success is True
        mock_excel.Quit.assert_called_once()
        mock_wb.ExportAsFixedFormat.assert_called_once()

def test_windows_excel_xlsm_conversion(converter):
    source = Path("test.xlsm")
    target = Path("test.xlsx")
    
    mock_excel = MagicMock()
    mock_wb = MagicMock()
    
    mock_win32com_client.Dispatch.return_value = mock_excel
    mock_excel.Workbooks.Open.return_value = mock_wb
    
    with patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.absolute", return_value=Path("/abs/test.xlsm")):
        
        result = converter.convert_xlsm_to_xlsx(source, target)
        
        assert result.success is True
        mock_wb.SaveAs.assert_called_once()
        mock_excel.Quit.assert_called_once()
