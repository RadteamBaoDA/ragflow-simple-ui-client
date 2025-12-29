"""
Typer CLI application for Simple UI client.

Provides commands for managing the background agent:
- start: Start the daemon in background
- stop: Stop the running daemon
- run: Run in foreground (debug mode)
- status: Check daemon status
- convert: Convert Office documents to PDF
"""

import asyncio
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from simple_ui_client import __version__
from simple_ui_client.cli.ui import (
    print_banner,
    print_status,
    print_success,
    print_error,
    print_info,
    print_warning,
)
from simple_ui_client.utils.config import get_settings


# Create Typer app
app = typer.Typer(
    name="simple-ui",
    help="Simple UI Client - A background agent for Simple UI",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold]Simple UI Client[/bold] v{__version__}")
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
    """Simple UI Client - Connect to Simple UI backend via Socket.IO."""
    pass


@app.command()
def start(
    foreground: Annotated[
        bool,
        typer.Option("--foreground", "-f", help="Run in foreground instead of daemon"),
    ] = False,
) -> None:
    """Start the Simple UI client daemon."""
    settings = get_settings()
    
    print_banner()
    
    if foreground:
        # Run in foreground (same as 'run' command)
        run_impl(daemon_child=False)
        return
    
    from simple_ui_client.core.daemon import Daemon, DaemonError
    
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
    """Stop the running Simple UI client daemon."""
    settings = get_settings()
    
    from simple_ui_client.core.daemon import Daemon, DaemonError
    
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
    """Run the Simple UI client in foreground (debug mode)."""
    run_impl(daemon_child=daemon_child)


def run_impl(daemon_child: bool = False) -> None:
    """Implementation for running the client."""
    settings = get_settings()
    
    if not daemon_child:
        print_banner()
        print_info(f"Server: {settings.websocket_url}")
        print_info(f"Log level: {settings.log_level}")
        print_info("Press Ctrl+C to stop\n")
    
    from simple_ui_client.core.lifecycle import run_foreground
    from simple_ui_client.utils.logger import setup_logger
    
    # Setup logger
    setup_logger(settings, daemon_mode=daemon_child)
    
    try:
        asyncio.run(run_foreground(settings))
    except KeyboardInterrupt:
        if not daemon_child:
            print_info("\nShutting down...")


@app.command()
def status() -> None:
    """Check the status of the Simple UI client daemon."""
    settings = get_settings()
    
    from simple_ui_client.core.daemon import Daemon
    
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
    table.add_row("Simple UI Home", str(settings.simple_ui_home))
    table.add_row("PID File", str(settings.pid_file))
    table.add_row("Log Directory", str(settings.log_dir))
    table.add_row("Reconnect Max Delay", f"{settings.reconnect_max_delay}s")
    table.add_row("Ping Interval", f"{settings.ping_interval}s")
    table.add_row("Ping Timeout", f"{settings.ping_timeout}s")
    
    console.print()
    console.print(table)


@app.command()
def convert(
    input_dir: Annotated[
        Path,
        typer.Argument(
            help="Input directory containing Office documents (default: ./input)",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("./input"),
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output", "-o",
            help="Output directory for PDFs (default: ./output)",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("./output"),
    config_file: Annotated[
        Optional[Path],
        typer.Option(
            "--config", "-c",
            help="Path to config.yaml file",
        ),
    ] = None,
    workers: Annotated[
        int,
        typer.Option(
            "--workers", "-w",
            help="Number of parallel workers",
            min=1,
            max=32,
        ),
    ] = 4,
    timeout: Annotated[
        int,
        typer.Option(
            "--timeout", "-t",
            help="Timeout per file in minutes",
            min=1,
            max=120,
        ),
    ] = 30,
    keep_temp: Annotated[
        bool,
        typer.Option(
            "--keep-temp",
            help="Keep temporary files after conversion",
        ),
    ] = False,
) -> None:
    """Convert Office documents (Word, Excel, PowerPoint) to PDF."""
    from pathlib import Path as PathLib
    
    from simple_ui_client.features.doc_converter.core.prerequisite import (
        check_prerequisites,
        PrerequisiteError,
    )
    from simple_ui_client.features.doc_converter.config.converter_config import ConverterConfig
    from simple_ui_client.features.doc_converter.core.output_manager import (
        OutputManager,
        discover_files,
    )
    from simple_ui_client.features.doc_converter.worker.batch_worker import BatchWorker
    from simple_ui_client.features.doc_converter.ui.progress_ui import ProgressManager
    from simple_ui_client.utils.logger import setup_logger
    
    # Initialize settings and logger
    settings = get_settings()
    setup_logger(settings, daemon_mode=False)
    
    print_banner()
    
    # Check prerequisites
    print_info("Checking prerequisites...")
    try:
        status = check_prerequisites()
        print_success(f"Found: {status.message}")
    except PrerequisiteError as e:
        print_error(str(e))
        raise typer.Exit(1)
    
    # Load configuration
    print_info("Loading configuration...")
    try:
        config = ConverterConfig.load(config_file)
        
        # Override settings log_dir if specified in YAML
        if config.logging.log_dir:
            settings.log_dir = config.logging.log_dir
            # Re-initialize logger with new directory
            setup_logger(settings, daemon_mode=False)
        
        # Override with CLI options
        config.conversion.workers = workers
        config.conversion.timeout_minutes = timeout
        config.conversion.keep_temp_files = keep_temp
        
        print_success("Configuration loaded")
    except Exception as e:
        print_error(f"Failed to load config: {e}")
        raise typer.Exit(1)
    
    # Discover files
    if not input_dir.exists():
        print_info(f"Input directory does not exist, creating: {input_dir}")
        input_dir.mkdir(parents=True, exist_ok=True)
        
    print_info(f"Scanning {input_dir}...")
    files = discover_files(input_dir)
    
    if not files:
        print_warning(f"No Office documents found in {input_dir}")
        raise typer.Exit(0)
    
    print_success(f"Found {len(files)} documents")
    
    # Setup output
    output_manager = OutputManager(
        input_dir=input_dir,
        output_dir=output_dir,
        suffix_config=config.conversion.suffixes,
        keep_temp=keep_temp,
    )
    
    print_info(f"Output directory: {output_dir}")
    
    # Run conversion
    try:
        with ProgressManager(
            total_files=len(files),
            log_lines=config.logging.log_console_lines,
        ) as progress:
            worker = BatchWorker(config, progress)
            result = asyncio.run(worker.process_batch(files, output_manager))
        
        # Print summary
        console.print()
        if result.failed == 0:
            print_success(
                f"Conversion complete: {result.successful}/{result.total_files} files "
                f"in {result.duration_seconds:.1f}s"
            )
        else:
            print_warning(
                f"Conversion complete with errors: {result.successful} succeeded, "
                f"{result.failed} failed in {result.duration_seconds:.1f}s"
            )
        
        if result.summary_path:
            print_info(f"Summary report: {result.summary_path}")
            
    except KeyboardInterrupt:
        print_warning("\nConversion cancelled by user")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Conversion failed: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
