"""Unit tests for file watcher."""
import time
from pathlib import Path
from mdreader.utils.file_watcher import FileWatcher


def test_file_watcher_detects_change(tmp_path: Path):
    test_file = tmp_path / "test.md"
    test_file.write_text("# Initial Content", encoding="utf-8")

    called = []

    def on_change():
        called.append(True)

    watcher = FileWatcher(filepath=test_file, on_modified=on_change, poll_interval=0.1)
    watcher.start()

    try:
        # Give initial thread time to start
        time.sleep(0.2)
        # Modify file
        test_file.write_text("# Updated Content", encoding="utf-8")
        # Give poll time to detect
        time.sleep(0.3)
        assert len(called) >= 1
    finally:
        watcher.stop()
