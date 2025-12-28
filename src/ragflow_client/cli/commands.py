"""
Typer CLI application for RAGFlow client.

Provides commands for managing the background agent:
- start: Start the daemon in background
- stop: Stop the running daemon
- run: Run in foreground (debug mode)
- status: Check daemon status
"""

import asyncio
import sys
from typing import Annotated, Optional

import typer
from rich.console import Console

from ragflow_client import __version__
from ragflow_client.cli.ui import (
    print_banner,
    print_status,
    print_success,
    print_error,
    print_info,
)
from ragflow_client.utils.config import get_settings


# Create Typer app
app = typer.Typer(
    name="ragflow",
    help="RAGFlow Client - A background agent for RAGFlow",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold]RAGFlow Client[/bold] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version", "-v",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """RAGFlow Client - Connect to RAGFlow backend via Socket.IO."""
    pass


@app.command()
def start(
    foreground: Annotated[
        bool,
        typer.Option("--foreground", "-f", help="Run in foreground instead of daemon"),
    ] = False,
) -> None:
    """Start the RAGFlow client daemon."""
    settings = get_settings()
    
    print_banner()
    
    if foreground:
        # Run in foreground (same as 'run' command)
        run_impl(daemon_child=False)
        return
    
    from ragflow_client.core.daemon import Daemon, DaemonError
    
    daemon = Daemon(settings)
    
    try:
        if daemon.is_running():
            status = daemon.get_status()
            print_error(f"Daemon already running (PID: {status['pid']})")
            raise typer.Exit(1)
        
        print_info("Starting daemon...")
        daemon.start()
        
        # Give it a moment to start
        import time
        time.sleep(0.5)
        
        if daemon.is_running():
            status = daemon.get_status()
            print_success(f"Daemon started (PID: {status['pid']})")
        else:
            print_error("Daemon failed to start. Check logs for details.")
            raise typer.Exit(1)
            
    except DaemonError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def stop() -> None:
    """Stop the running RAGFlow client daemon."""
    settings = get_settings()
    
    from ragflow_client.core.daemon import Daemon, DaemonError
    
    daemon = Daemon(settings)
    
    try:
        if daemon.stop():
            print_success("Daemon stopped")
        else:
            print_info("No daemon running")
            
    except DaemonError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def run(
    daemon_child: Annotated[
        bool,
        typer.Option("--daemon-child", hidden=True, help="Internal flag for daemon child process"),
    ] = False,
) -> None:
    """Run the RAGFlow client in foreground (debug mode)."""
    run_impl(daemon_child=daemon_child)


def run_impl(daemon_child: bool = False) -> None:
    """Implementation for running the client."""
    settings = get_settings()
    
    if not daemon_child:
        print_banner()
        print_info(f"Server: {settings.websocket_url}")
        print_info(f"Log level: {settings.log_level}")
        print_info("Press Ctrl+C to stop\n")
    
    from ragflow_client.core.lifecycle import run_foreground
    from ragflow_client.utils.logger import setup_logger
    
    # Setup logger
    setup_logger(settings, daemon_mode=daemon_child)
    
    try:
        asyncio.run(run_foreground(settings))
    except KeyboardInterrupt:
        if not daemon_child:
            print_info("\nShutting down...")


@app.command()
def status() -> None:
    """Check the status of the RAGFlow client daemon."""
    settings = get_settings()
    
    from ragflow_client.core.daemon import Daemon
    
    daemon = Daemon(settings)
    status_info = daemon.get_status()
    
    print_status(status_info)


@app.command()
def config() -> None:
    """Show current configuration."""
    settings = get_settings()
    
    from rich.table import Table
    
    table = Table(title="Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="dim")
    table.add_column("Value")
    
    table.add_row("WebSocket URL", settings.websocket_url)
    table.add_row("API Key", "***" if settings.websocket_api_key else "(not set)")
    table.add_row("User Email", settings.user_email or "(not set)")
    table.add_row("Log Level", settings.log_level)
    table.add_row("JSON Logs", str(settings.json_logs))
    table.add_row("RAGFlow Home", str(settings.ragflow_home))
    table.add_row("PID File", str(settings.pid_file))
    table.add_row("Log Directory", str(settings.log_dir))
    table.add_row("Reconnect Max Delay", f"{settings.reconnect_max_delay}s")
    table.add_row("Ping Interval", f"{settings.ping_interval}s")
    table.add_row("Ping Timeout", f"{settings.ping_timeout}s")
    
    console.print()
    console.print(table)


if __name__ == "__main__":
    app()
