"""
Entry point for running the RAGFlow client as a module.

Usage:
    python -m ragflow_client [COMMAND] [OPTIONS]
"""

from ragflow_client.cli.commands import app

if __name__ == "__main__":
    app()
