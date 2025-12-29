# Simple UI Client

A modern, cross-platform background agent for Simple UI.

## Features

- **Socket.IO Connection**: Real-time bi-directional communication with Simple UI backend
- **Event-Driven Architecture**: Internal async event bus for decoupled feature logic
- **Document Conversion**: Built-in micro-service for document processing
- **Cross-Platform Daemon**: Background execution on Windows, macOS, and Linux
- **CLI Management**: Typer-based commands for easy control

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Start the daemon in background
simple-client start

# Run in foreground (debug mode)
simple-client run

# Check status
simple-client status

# Stop the daemon
simple-client stop

# Show configuration
simple-client config
```

## Document Conversion

The client includes a standalone CLI for batch converting Office documents to PDF:

```bash
# Using developmemt script
python src/main.py convert ./input --output ./output

# Using python module
python -m simple_ui_client convert ./input --output ./output
```

For detailed options and prerequisites, see the [Converter Guide](CONVERTER_GUIDE.md).

## Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Required settings:
- `WEBSOCKET_API_KEY`: API key for authentication
- `WEBSOCKET_URL`: WebSocket server URL

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/simple_ui_client
```

## License

MIT
