---
description: init
---

1. Foundation: Setup pyproject.toml and utils/config.py.

2. Internal Bus: Implement the Asyncio.Queue dispatcher in core/bus.py.

3. Daemon: Build the cross-platform background logic in core/daemon.py.

4. Networking: Implement the SocketService with reconnection logic.

5. Feature Worker: Build the doc_converter micro-module and register it to the bus.

6. CLI Binding: Connect everything to the Typer app in cli/commands.py.