"""
Entry point for running the Simple UI client as a module.

Usage:
    python -m simple_ui_client [COMMAND] [OPTIONS]
"""

from simple_ui_client.cli.commands import app

if __name__ == "__main__":
    app()
