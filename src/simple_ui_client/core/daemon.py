"""
Cross-platform daemon management.

Provides background execution support for:
- Unix (Linux/MacOS): Double-fork strategy with PID file
- Windows: Detached process with CREATE_NEW_PROCESS_GROUP
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from simple_ui_client.utils.config import Settings


class DaemonError(Exception):
    """Exception raised for daemon-related errors."""
    pass


class Daemon:
    """
    Cross-platform daemon manager.
    
    Handles starting, stopping, and status checking of the background process.
    Uses platform-specific strategies for backgrounding.
    """
    
    def __init__(self, settings: "Settings") -> None:
        """
        Initialize the daemon manager.
        
        Args:
            settings: Application settings containing PID file path.
        """
        self.settings = settings
        self.pid_file = settings.pid_file
        self._logger = logger.bind(component="Daemon")
    
    def start(self) -> None:
        """
        Start the daemon in background mode.
        
        Raises:
            DaemonError: If daemon is already running or failed to start.
        """
        if self.is_running():
            pid = self._read_pid()
            raise DaemonError(f"Daemon already running (PID: {pid})")
        
        self.settings.ensure_directories()
        
        if sys.platform == "win32":
            self._start_windows()
        else:
            self._start_unix()
    
    def stop(self) -> bool:
        """
        Stop the running daemon.
        
        Returns:
            True if daemon was stopped, False if it wasn't running.
            
        Raises:
            DaemonError: If failed to stop the daemon.
        """
        pid = self._read_pid()
        if pid is None:
            self._logger.info("No daemon running")
            return False
        
        try:
            if sys.platform == "win32":
                self._stop_windows(pid)
            else:
                self._stop_unix(pid)
            
            self._cleanup_pid_file()
            self._logger.info(f"Daemon stopped (PID: {pid})")
            return True
            
        except ProcessLookupError:
            self._logger.warning(f"Process {pid} not found, cleaning up PID file")
            self._cleanup_pid_file()
            return False
        except Exception as e:
            raise DaemonError(f"Failed to stop daemon: {e}") from e
    
    def is_running(self) -> bool:
        """
        Check if the daemon is currently running.
        
        Returns:
            True if daemon is running, False otherwise.
        """
        pid = self._read_pid()
        if pid is None:
            return False
        
        return self._process_exists(pid)
    
    def get_status(self) -> dict[str, str | int | None]:
        """
        Get the current daemon status.
        
        Returns:
            Dictionary with status information.
        """
        pid = self._read_pid()
        running = pid is not None and self._process_exists(pid)
        
        return {
            "status": "running" if running else "stopped",
            "pid": pid if running else None,
            "pid_file": str(self.pid_file),
        }
    
    def _start_unix(self) -> None:
        """Start daemon on Unix using double-fork strategy."""
        self._logger.info("Starting daemon (Unix mode)...")
        
        # First fork
        try:
            pid = os.fork()
            if pid > 0:
                # Parent exits
                self._logger.info(f"First fork successful, parent exiting")
                return
        except OSError as e:
            raise DaemonError(f"First fork failed: {e}") from e
        
        # Decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)
        
        # Second fork
        try:
            pid = os.fork()
            if pid > 0:
                # First child exits
                sys.exit(0)
        except OSError as e:
            raise DaemonError(f"Second fork failed: {e}") from e
        
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        
        with open(os.devnull, 'r') as devnull_r:
            os.dup2(devnull_r.fileno(), sys.stdin.fileno())
        with open(os.devnull, 'a+') as devnull_w:
            os.dup2(devnull_w.fileno(), sys.stdout.fileno())
            os.dup2(devnull_w.fileno(), sys.stderr.fileno())
        
        # Write PID file
        self._write_pid(os.getpid())
        
        # Run the main loop (this is now the daemon process)
        self._run_daemon_main()
    
    def _start_windows(self) -> None:
        """Start daemon on Windows using detached process."""
        self._logger.info("Starting daemon (Windows mode)...")
        
        # Build command to run the client in daemon mode
        python_exe = sys.executable
        module_args = ["-m", "simple_ui_client", "run", "--daemon-child"]
        
        # Windows-specific process creation flags
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        
        try:
            process = subprocess.Popen(
                [python_exe, *module_args],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                start_new_session=True,
            )
            
            self._write_pid(process.pid)
            self._logger.info(f"Daemon started (PID: {process.pid})")
            
        except Exception as e:
            raise DaemonError(f"Failed to start Windows daemon: {e}") from e
    
    def _stop_unix(self, pid: int) -> None:
        """Stop daemon on Unix by sending SIGTERM."""
        import signal
        os.kill(pid, signal.SIGTERM)
    
    def _stop_windows(self, pid: int) -> None:
        """Stop daemon on Windows by terminating the process."""
        import signal
        os.kill(pid, signal.SIGTERM)
    
    def _process_exists(self, pid: int) -> bool:
        """Check if a process with the given PID exists."""
        try:
            if sys.platform == "win32":
                # Windows: Use tasklist
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}"],
                    capture_output=True,
                    text=True,
                )
                return str(pid) in result.stdout
            else:
                # Unix: Send signal 0
                os.kill(pid, 0)
                return True
        except (OSError, ProcessLookupError):
            return False
    
    def _read_pid(self) -> int | None:
        """Read PID from file."""
        try:
            if self.pid_file.exists():
                content = self.pid_file.read_text().strip()
                return int(content) if content else None
        except (ValueError, IOError):
            pass
        return None
    
    def _write_pid(self, pid: int) -> None:
        """Write PID to file."""
        self.pid_file.write_text(str(pid))
        self._logger.debug(f"Wrote PID {pid} to {self.pid_file}")
    
    def _cleanup_pid_file(self) -> None:
        """Remove the PID file."""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
                self._logger.debug(f"Removed PID file: {self.pid_file}")
        except IOError as e:
            self._logger.warning(f"Failed to remove PID file: {e}")
    
    def _run_daemon_main(self) -> None:
        """
        Run the main daemon loop.
        
        This is called after forking on Unix systems.
        """
        # Import here to avoid circular imports
        from simple_ui_client.core.lifecycle import LifecycleManager
        from simple_ui_client.utils.config import get_settings
        from simple_ui_client.utils.logger import setup_logger
        
        import asyncio
        
        # Re-initialize settings and logger for daemon process
        settings = get_settings()
        setup_logger(settings, daemon_mode=True)
        
        self._logger.info(f"Daemon process started (PID: {os.getpid()})")
        
        # Run the main application loop
        lifecycle = LifecycleManager(settings)
        
        try:
            asyncio.run(lifecycle.run())
        except KeyboardInterrupt:
            self._logger.info("Daemon interrupted")
        except Exception as e:
            self._logger.exception(f"Daemon crashed: {e}")
        finally:
            self._cleanup_pid_file()
