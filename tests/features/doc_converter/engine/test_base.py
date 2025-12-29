from pathlib import Path
from ragflow_client.features.doc_converter.engine.base import ConversionResult

def test_conversion_result_defaults():
    source = Path("input.docx")
    result = ConversionResult(success=True, source_path=source)
    
    assert result.success is True
    assert result.source_path == source
    assert result.output_path is None
    assert result.duration_seconds == 0.0
    assert result.pages == 0
    assert result.metadata == {}

def test_conversion_result_full():
    source = Path("input.docx")
    target = Path("output.pdf")
    result = ConversionResult(
        success=True,
        source_path=source,
        output_path=target,
        duration_seconds=1.5,
        pages=10,
        metadata={"author": "test"}
    )
    
    assert result.success is True
    assert result.output_path == target
    assert result.duration_seconds == 1.5
    assert result.pages == 10
    assert result.metadata["author"] == "test"
