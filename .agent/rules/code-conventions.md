---
trigger: always_on
---

# CODE_CONVENTIONS.md

## 1. Python 3.12+ Standards
- **Typing:** Use the new `type` statement for type aliases.
- `type ProgressValue = int | float`
- **Strict Typing:** Every function must have a return type hint. Use `Self` for class methods returning the instance.
- **Modern f-strings:** Use nested f-strings for complex log formatting.

## 2. Asynchronous Patterns
- **Concurrency:** Never use blocking calls like `time.sleep` or `requests`. Use `asyncio.sleep` and `aiohttp/httpx`.
- **Heartbeat Protection:** Any task taking longer than 1 second must be run in a separate thread using `asyncio.to_thread` or a ProcessPool to avoid blocking the Socket.IO loop.
- **Lifecycle:** Use `asyncio.TaskGroup` for managing related background tasks.

## 3. Error Handling
- **No Broad Catches:** Never use `except:`. Always catch specific exceptions (e.g., `socketio.exceptions.ConnectionError`).
- **Graceful Shutdown:** All components must handle `asyncio.CancelledError` to clean up resources (temp files, open sockets).
- **Socket Backoff:** Implement an exponential backoff strategy (1s, 2s, 4s... up to 60s) for server reconnections.

## 4. Logging & Pathing
- **Logging:** Use `loguru` exclusively. Logs should be JSON-formatted in production (daemon mode).
- **Paths:** Always use `pathlib.Path`. Cross-platform paths (e.g., for `~/.ragflow`) must be handled correctly using `Path.home()`.

## 5. Event Bus Protocol
- **Event Naming:** Use `feature:action` format (e.g., `doc:convert`, `sys:shutdown`).
- **Payloads:** All internal events must pass data using Pydantic models for validation.