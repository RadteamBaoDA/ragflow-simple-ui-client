"""
CLI module for RAGFlow client.

Provides command-line interface using Typer with commands for
managing the background agent.
"""

from ragflow_client.cli.commands import app

__all__ = ["app"]
