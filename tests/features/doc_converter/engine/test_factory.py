import sys
from unittest.mock import patch, MagicMock
import pytest
from simple_ui_client.features.doc_converter.engine.factory import get_converter, get_converter_info

def test_get_converter_windows():
    with patch("sys.platform", "win32"):
        with patch("simple_ui_client.features.doc_converter.engine.windows.WindowsConverter") as mock_conv:
            conv = get_converter()
            assert conv == mock_conv.return_value

def test_get_converter_linux():
    for platform in ["linux", "linux2", "darwin"]:
        with patch("sys.platform", platform):
            with patch("simple_ui_client.features.doc_converter.engine.linux.LinuxConverter") as mock_conv:
                conv = get_converter()
                assert conv == mock_conv.return_value

def test_get_converter_unsupported():
    with patch("sys.platform", "unsupported_os"):
        with pytest.raises(RuntimeError, match="No converter available"):
            get_converter()

def test_get_converter_info():
    with patch("sys.platform", "win32"):
        info = get_converter_info()
        assert info["platform"] == "Windows"
        assert "Microsoft Office" in info["converter"]

    with patch("sys.platform", "linux"):
        info = get_converter_info()
        assert info["platform"] == "Linux"
        assert "LibreOffice" in info["converter"]

    with patch("sys.platform", "darwin"):
        info = get_converter_info()
        assert info["platform"] == "macOS"
        assert "LibreOffice" in info["converter"]

    with patch("sys.platform", "unknown"):
        info = get_converter_info()
        assert info["converter"] == "Unknown"
