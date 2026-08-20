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

    screen = FilePickerScreen(start_dir=tmp_path)
    filenames = [p.name for p in screen.all_files]
    assert "doc1.md" in filenames
    assert "doc2.markdown" in filenames
    assert "ignored.txt" not in filenames
