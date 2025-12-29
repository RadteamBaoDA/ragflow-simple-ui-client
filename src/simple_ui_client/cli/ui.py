"""
Rich-based terminal UI utilities.

Provides styled output, status displays, progress bars, and tables
for the CLI interface.
"""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from simple_ui_client import __version__


console = Console()


def print_banner() -> None:
    """Print the application banner."""
    banner = Text()
    banner.append("Simple UI Client", style="bold cyan")
    banner.append(f" v{__version__}", style="dim")
    
    console.print()
    console.print(Panel(banner, border_style="cyan", padding=(0, 2)))
    console.print()


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]ℹ[/blue] {message}")


def print_status(status_info: dict[str, Any]) -> None:
    """
    Print daemon status in a formatted table.
    
    Args:
        status_info: Dictionary with status information.
    """
    is_running = status_info.get("status") == "running"
    
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value")
    
    # Status with color
    status_text = "[green]● Running[/green]" if is_running else "[red]● Stopped[/red]"
    table.add_row("Status", status_text)
    
    # PID
    pid = status_info.get("pid")
    table.add_row("PID", str(pid) if pid else "-")
    
    # PID file
    pid_file = status_info.get("pid_file", "")
    table.add_row("PID File", pid_file)
    
    console.print()
    console.print(Panel(table, title="Daemon Status", border_style="cyan"))
    console.print()


def create_progress_table(jobs: list[dict[str, Any]]) -> Table:
    """
    Create a table showing job progress.
    
    Args:
        jobs: List of job status dictionaries.
        
    Returns:
        Rich Table with job information.
    """
    table = Table(title="Active Jobs", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=8)
    table.add_column("Source")
    table.add_column("Progress")
    table.add_column("Status")
    
    for job in jobs:
        job_id = str(job.get("id", ""))[:8]
        source = job.get("source", "unknown")[:30]
        progress = job.get("progress", 0)
        status = job.get("status", "unknown")
        
        # Create progress bar
        bar_width = 20
        filled = int(bar_width * progress / 100)
        bar = f"[{'█' * filled}{'░' * (bar_width - filled)}] {progress}%"
        
        # Status color
        status_colors = {
            "pending": "yellow",
            "processing": "blue",
            "completed": "green",
            "failed": "red",
            "cancelled": "dim",
        }
        color = status_colors.get(status, "white")
        
        table.add_row(job_id, source, bar, f"[{color}]{status}[/{color}]")
    
    return table


def confirm(message: str, default: bool = False) -> bool:
    """
    Prompt for confirmation.
    
    Args:
        message: The confirmation message.
        default: Default value if user just presses Enter.
        
    Returns:
        True if confirmed, False otherwise.
    """
    suffix = "[Y/n]" if default else "[y/N]"
    response = console.input(f"{message} {suffix}: ").strip().lower()
    
    if not response:
        return default
    
    return response in ("y", "yes")
