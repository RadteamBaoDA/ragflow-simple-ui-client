"""
Progress UI for document conversion.

Provides Rich-based progress display with per-file and total ETA,
scrollable log stream, and multi-thread log aggregation.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text


@dataclass
class FileStatus:
    """Status of a single file being processed."""
    filename: str
    status: str = "pending"
    progress: int = 0
    started_at: float | None = None
    completed_at: float | None = None
    error: str | None = None


@dataclass
class LogEntry:
    """A log entry for the log stream."""
    timestamp: datetime
    level: str
    message: str
    thread: str = "main"


class ProgressManager:
    """
    Manages progress display for batch document conversions.
    
    Features:
    - Overall progress bar with file count
    - Per-file status display
    - Per-file and total ETA calculation
    - Scrollable log stream area
    - Thread-safe log aggregation
    
    Example:
        with ProgressManager(total_files=10) as pm:
            pm.start_file("document.docx")
            pm.update_file("document.docx", "converting", 50)
            pm.add_log("Processing page 1", "INFO")
            pm.complete_file("document.docx")
    """
    
    def __init__(
        self,
        total_files: int,
        log_lines: int = 20,
        console: Console | None = None,
    ) -> None:
        """
        Initialize the progress manager.
        
        Args:
            total_files: Total number of files to process.
            log_lines: Number of log lines to display.
            console: Rich console instance.
        """
        self.total_files = total_files
        self.log_lines = log_lines
        self.console = console or Console()
        
        # State
        self._files: dict[str, FileStatus] = {}
        self._logs: deque[LogEntry] = deque(maxlen=log_lines)
        self._completed_count = 0
        self._failed_count = 0
        self._start_time = time.time()
        self._lock = threading.Lock()
        
        # Progress bar
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console,
        )
        self._main_task: TaskID | None = None
        
        # Live display
        self._live: Live | None = None
    
    def __enter__(self) -> "ProgressManager":
        """Start the live display."""
        self._main_task = self._progress.add_task(
            "Converting files",
            total=self.total_files,
        )
        self._live = Live(
            self._create_layout(),
            console=self.console,
            refresh_per_second=4,
        )
        self._live.__enter__()
        return self
    
    def __exit__(self, *args: Any) -> None:
        """Stop the live display."""
        if self._live:
            self._live.__exit__(*args)
    
    def _create_layout(self) -> Panel:
        """Create the display layout."""
        # Progress section
        progress_panel = Panel(
            self._progress,
            title="[bold]Overall Progress[/bold]",
            border_style="blue",
        )
        
        # Active files section
        files_table = Table(show_header=True, header_style="bold cyan", box=None)
        files_table.add_column("File", style="dim", width=40)
        files_table.add_column("Status", width=15)
        files_table.add_column("Progress", width=15)
        files_table.add_column("ETA", width=10)
        
        with self._lock:
            for filename, status in list(self._files.items())[-5:]:  # Show last 5
                status_style = {
                    "pending": "yellow",
                    "converting": "blue",
                    "completed": "green",
                    "failed": "red",
                }.get(status.status, "white")
                
                # Calculate per-file ETA
                file_eta = "-"
                if status.status == "converting" and status.started_at:
                    elapsed = time.time() - status.started_at
                    if status.progress > 0:
                        remaining = (elapsed / status.progress) * (100 - status.progress)
                        file_eta = f"{remaining:.0f}s"
                
                progress_bar = self._make_progress_bar(status.progress)
                
                files_table.add_row(
                    filename[:38] + ".." if len(filename) > 40 else filename,
                    f"[{status_style}]{status.status}[/{status_style}]",
                    progress_bar,
                    file_eta,
                )
        
        files_panel = Panel(
            files_table,
            title="[bold]Active Files[/bold]",
            border_style="cyan",
        )
        
        # Stats section
        stats = self._calculate_stats()
        stats_text = Text()
        stats_text.append(f"Completed: ", style="dim")
        stats_text.append(f"{self._completed_count}", style="green bold")
        stats_text.append(f"  Failed: ", style="dim")
        stats_text.append(f"{self._failed_count}", style="red bold")
        stats_text.append(f"  Remaining: ", style="dim")
        stats_text.append(f"{self.total_files - self._completed_count - self._failed_count}", style="yellow bold")
        stats_text.append(f"  Total ETA: ", style="dim")
        stats_text.append(f"{stats['total_eta']}", style="cyan bold")
        
        # Logs section
        log_lines = []
        with self._lock:
            for entry in self._logs:
                level_style = {
                    "DEBUG": "dim",
                    "INFO": "blue",
                    "WARNING": "yellow",
                    "ERROR": "red",
                }.get(entry.level, "white")
                
                log_lines.append(
                    f"[dim]{entry.timestamp.strftime('%H:%M:%S')}[/dim] "
                    f"[{level_style}]{entry.level:5}[/{level_style}] "
                    f"{entry.message}"
                )
        
        logs_text = "\n".join(log_lines) if log_lines else "[dim]No logs yet[/dim]"
        logs_panel = Panel(
            logs_text,
            title="[bold]Log Stream[/bold]",
            border_style="dim",
            height=min(self.log_lines + 2, 25),
        )
        
        # Combine all sections
        return Panel(
            Group(
                progress_panel,
                stats_text,
                files_panel,
                logs_panel,
            ),
            title="[bold white]Document Converter[/bold white]",
            border_style="white",
        )
    
    def _make_progress_bar(self, progress: int) -> str:
        """Create a simple progress bar string."""
        filled = int(progress / 10)
        return f"[green]{'█' * filled}[/green][dim]{'░' * (10 - filled)}[/dim] {progress}%"
    
    def _calculate_stats(self) -> dict[str, str]:
        """Calculate overall statistics."""
        completed = self._completed_count + self._failed_count
        remaining = self.total_files - completed
        
        if completed == 0:
            total_eta = "calculating..."
        else:
            elapsed = time.time() - self._start_time
            avg_time = elapsed / completed
            eta_seconds = avg_time * remaining
            
            if eta_seconds < 60:
                total_eta = f"{eta_seconds:.0f}s"
            elif eta_seconds < 3600:
                total_eta = f"{eta_seconds / 60:.1f}m"
            else:
                total_eta = f"{eta_seconds / 3600:.1f}h"
        
        return {"total_eta": total_eta}
    
    def _update_display(self) -> None:
        """Update the live display."""
        if self._live:
            self._live.update(self._create_layout())
    
    def start_file(self, filename: str) -> None:
        """Mark a file as started."""
        with self._lock:
            self._files[filename] = FileStatus(
                filename=filename,
                status="converting",
                started_at=time.time(),
            )
        self._update_display()
    
    def update_file(self, filename: str, status: str, progress: int) -> None:
        """Update file status and progress."""
        with self._lock:
            if filename in self._files:
                self._files[filename].status = status
                self._files[filename].progress = progress
        self._update_display()
    
    def complete_file(self, filename: str, success: bool = True, error: str | None = None) -> None:
        """Mark a file as completed."""
        with self._lock:
            if filename in self._files:
                self._files[filename].status = "completed" if success else "failed"
                self._files[filename].progress = 100 if success else self._files[filename].progress
                self._files[filename].completed_at = time.time()
                self._files[filename].error = error
            
            if success:
                self._completed_count += 1
            else:
                self._failed_count += 1
        
        if self._main_task is not None:
            self._progress.update(self._main_task, advance=1)
        
        self._update_display()
    
    def add_log(self, message: str, level: str = "INFO", thread: str = "main") -> None:
        """Add a log entry to the stream."""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            thread=thread,
        )
        with self._lock:
            self._logs.append(entry)
        self._update_display()
    
    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the conversion process."""
        elapsed = time.time() - self._start_time
        
        return {
            "total_files": self.total_files,
            "completed": self._completed_count,
            "failed": self._failed_count,
            "elapsed_seconds": elapsed,
            "files": {
                name: {
                    "status": f.status,
                    "error": f.error,
                    "duration": (
                        f.completed_at - f.started_at
                        if f.completed_at and f.started_at
                        else None
                    ),
                }
                for name, f in self._files.items()
            },
        }
