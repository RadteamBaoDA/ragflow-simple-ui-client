from pathlib import Path
import pytest
import yaml
from simple_ui_client.features.doc_converter.config.converter_config import ConverterConfig, Orientation, SheetConfig

def test_load_default_config():
    config = ConverterConfig()
    assert config.conversion.workers == 4
    assert config.word.default.orientation == Orientation.PORTRAIT

def test_load_from_yaml(temp_dir):
    config_data = {
        "conversion": {
            "workers": 8,
            "timeout_minutes": 60
        },
        "word": {
            "default": {
                "orientation": "landscape"
            }
        },
        "excel": {
            "sheets": [
                {"names": ["Summary"], "scaling": "fit_sheet", "priority": 1}
            ]
        }
    }
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
        
    config = ConverterConfig.load(config_path)
    assert config.conversion.workers == 8
    assert config.word.default.orientation == Orientation.LANDSCAPE
    assert len(config.excel.sheets) == 1
    assert config.excel.sheets[0].priority == 1

def test_get_config_for_sheet():
    config = ConverterConfig()
    config.excel.sheets = [
        SheetConfig(names=["Data*"], scaling="fit_columns", priority=2),
        SheetConfig(names=["Summary"], scaling="fit_sheet", priority=1)
    ]
    
    # Priority 1 should win for Summary
    sheet_config = config.excel.get_config_for_sheet("Summary")
    assert sheet_config.scaling == "fit_sheet"
    
    # Wildcard match
    sheet_config = config.excel.get_config_for_sheet("Data_Warehouse")
    assert sheet_config.scaling == "fit_columns"
    
    # Default
    sheet_config = config.excel.get_config_for_sheet("Random")
    assert sheet_config.scaling == config.excel.default.scaling
