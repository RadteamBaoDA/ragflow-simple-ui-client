---
trigger: always_on
---

# Agent Instructions: RAGFlow Simple UI Python Client

## 1. Role & System Context
You are an expert Systems Engineer and Python Architect. Your goal is to build a modern, cross-platform background agent that connects to a RAGFlow backend via Socket.IO. The tool must be robust, event-driven, and modularized to handle features like "Document Conversion" as internal micro-services.

## 2. Technical Stack Requirements
- **Runtime:** Python 3.12+ (Use PEP 695 Type Aliases, `asyncio`, and `Self`).
- **CLI:** `Typer` for command-line interface management.
- **WebSocket:** `python-socketio[asyncio_client]` for real-time bi-directional communication.
- **Service Management:** Custom daemon logic for Windows, MacOS, and Linux.
- **Feature Logic:** High-concurrency document processing.

---

## 3. Project Structure (Microservice Architecture)

```text
ragflow-client/
├── pyproject.toml              # Build system (use hatchling or pdm-backend)
├── .env.example                # Template for WEBSOCKET_API_KEY
├── src/
│   └── ragflow_client/
│       ├── __init__.py
│       ├── __main__.py          # Entry point (python -m ragflow_client)
│       ├── cli/                 # CLI Interface
│       │   ├── commands.py      # start, stop, run, status
│       │   └── ui.py            # Rich/Terminal formatting
│       ├── core/                # System Level Logic
│       │   ├── bus.py           # Internal Async Event Bus (Pub/Sub)
│       │   ├── daemon.py        # OS-Specific Background logic
│       │   └── lifecycle.py     # Signal handling (SIGTERM/SIGINT)
│       ├── features/            # Feature-based "Microservices"
│       │   └── doc_converter/   # Document Conversion Feature
│       │       ├── __init__.py
│       │       ├── processor.py # CPU-bound file processing (PDF/Docx)
│       │       ├── schema.py    # Job models (Pydantic)
│       │       └── worker.py    # Bus subscriber & job executor
│       ├── services/            # Infrastructure Services
│       │   ├── socket_service.py # WebSocket/Socket.IO logic
│       │   └── file_manager.py  # Temp file handling
│       └── utils/
│           ├── config.py        # Pydantic-Settings & Env validation
│           └── logger.py        # Structured Loguru setup
└── logs/                       # Rotating log files for daemon mode


## 4. Key Implementation Directives
### A. Daemon Mode (Cross-Platform)
The tool must support background execution without a persistent terminal:

Unix (Linux/MacOS): Use a double-fork strategy. Redirect stdin/stdout/stderr to os.devnull and maintain a PID file in ~/.ragflow/client.pid.

Windows: Use subprocess.DETACHED_PROCESS and CREATE_NEW_PROCESS_GROUP flags. Ensure the agent can be managed via the CLI even when running in the background.

### B. Internal Event Bus (Event-Driven Design)
Implement a non-blocking asyncio.Queue based event bus in core/bus.py to decouple network events from feature logic:

SocketService receives notification -> Publishes JobReceivedEvent.

DocConverterWorker subscribes to JobReceivedEvent -> Starts processor.py.

DocConverterWorker publishes JobProgressEvent -> SocketService relays to Server.

### C. WebSocket Authentication & Resilience
Auth: Pass the apiKey and optional email in the auth payload during connection as per server docs.

Resilience: Implement exponential backoff for reconnection. Ensure the ping_interval and ping_timeout match the server's configuration (25s / 60s).

## D. Document Conversion Feature
Use asyncio.to_thread for processor.py logic to prevent blocking the WebSocket heartbeat during heavy CPU tasks.

Implement progress reporting (e.g., 0%, 20%, 100%) through the WebSocket notification payload or a custom progress event.
