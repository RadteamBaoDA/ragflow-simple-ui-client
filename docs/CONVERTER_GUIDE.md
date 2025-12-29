# Simple UI Document Converter Guide

The Simple UI Client includes a powerful document conversion micro-service that can transform Office documents (Word, Excel, PowerPoint) into high-quality PDFs, preserving layout and formatting.

## 1. Running in CLI Mode (Development)

If you are working in the repository and haven't installed the package globally, use `src/main.py`:

### Basic Usage
```bash
python src/main.py convert
```
*Note: This defaults to `./input` and `./output`. Directories are created automatically if missing.*

### Examples
Convert with custom workers:
```bash
python src/main.py convert --workers 8
```

## 2. Command Options

| Option | Shorthand | Description | Default |
|--------|-----------|-------------|---------|
| `input_dir` | (arg) | Directory to scan for documents | `./input` |
| `--output` | `-o` | Output directory for PDF files | `./output` |
| `--workers` | `-w` | Number of parallel workers | 4 |
| `--timeout` | `-t` | Timeout in minutes | 30 |
| `--config` | `-c` | Custom `config.yaml` path | `None` |

## 3. Testing

To run the unit test suite:
```bash
pytest tests -v
```

## 4. Supported Formats

- **Word**: `.doc`, `.docx`, `.rtf`
- **Excel**: `.xls`, `.xlsx`, `.csv`, `.xlsm`
- **PowerPoint**: `.ppt`, `.pptx`

## 5. Prerequisites

- **Windows**: Microsoft Office (Word, Excel, PowerPoint)
- **Linux**: LibreOffice (`soffice`)
