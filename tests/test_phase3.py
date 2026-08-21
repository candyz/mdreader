"""Unit tests for graphics protocol helper and file picker scan."""
from pathlib import Path
from mdreader.renderer.graphics import is_iterm2_supported, is_kitty_supported, encode_iterm2_image
from mdreader.widgets.file_picker import FilePickerScreen


def test_graphics_protocol_detection(monkeypatch):
    monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
    assert is_iterm2_supported() is True

    monkeypatch.setenv("TERM_PROGRAM", "Apple_Terminal")
    assert is_iterm2_supported() is False

    monkeypatch.setenv("TERM_PROGRAM", "ghostty")
    assert is_kitty_supported() is True


def test_encode_iterm2_image(tmp_path: Path):
    sample = tmp_path / "test.png"
    sample.write_bytes(b"dummy image content")
    encoded = encode_iterm2_image(sample)
    assert encoded.startswith("\033]1337;File=inline=1;size=")
    assert encoded.endswith("\a")


def test_file_picker_scan(tmp_path: Path):
    (tmp_path / "doc1.md").write_text("# Doc 1", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "doc2.markdown").write_text("# Doc 2", encoding="utf-8")
    (tmp_path / "sub" / "ignored.txt").write_text("ignore", encoding="utf-8")

    # Default: only md / html files
    screen = FilePickerScreen(start_dir=tmp_path, show_all_files=False)
    screen._scan_directory()
    item_labels = [label for label, item_type, path in screen.items]
    assert any("doc1.md" in l for l in item_labels)
    assert any("sub/" in l for l in item_labels)
    assert not any("ignored.txt" in l for l in item_labels)

    # Show all files: includes .txt and other plain text
    screen_all = FilePickerScreen(start_dir=tmp_path / "sub", show_all_files=True)
    screen_all._scan_directory()
    item_labels_all = [label for label, item_type, path in screen_all.items]
    assert any("doc2.markdown" in l for l in item_labels_all)
    assert any("ignored.txt" in l for l in item_labels_all)
