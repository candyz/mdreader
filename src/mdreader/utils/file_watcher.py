"""File watcher utility for hot-reloading markdown files."""
import time
from pathlib import Path
from typing import Callable
from threading import Thread, Event


class FileWatcher:
    """Watches a local file for modification timestamps and invokes a callback."""

    def __init__(self, filepath: Path | str, on_modified: Callable[[], None], poll_interval: float = 0.5):
        self.filepath = Path(filepath)
        self.on_modified = on_modified
        self.poll_interval = poll_interval
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._last_mtime: float | None = None
        self._update_mtime()

    def _update_mtime(self) -> None:
        try:
            if self.filepath.exists():
                self._last_mtime = self.filepath.stat().st_mtime
        except Exception:
            pass

    def start(self) -> None:
        """Start the background polling thread."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background polling thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _run(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(self.poll_interval)
            try:
                if self.filepath.exists():
                    current_mtime = self.filepath.stat().st_mtime
                    if self._last_mtime is not None and current_mtime > self._last_mtime:
                        self._last_mtime = current_mtime
                        self.on_modified()
                    elif self._last_mtime is None:
                        self._last_mtime = current_mtime
            except Exception:
                pass
