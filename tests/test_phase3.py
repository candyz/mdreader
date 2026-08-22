"""Unit tests for graphics protocol helper and file picker scan."""
from pathlib import Path
from mdreader.renderer.graphics import is_iterm2_supported, is_kitty_supported, encode_iterm2_image
from mdreader.widgets.file_picker import FilePickerScreen


def test_graphics_protocol_detection(monkeypatch):
    monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
    monkeypatch.setenv("LC_TERMINAL", "iTerm2")
    assert is_iterm2_supported() is True

    monkeypatch.setenv("TERM_PROGRAM", "Apple_Terminal")
    monkeypatch.setenv("LC_TERMINAL", "")
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

    # Show all files: includes .txt and other plain text and dotfiles
    (tmp_path / "sub" / ".vimrc").write_text("syntax on", encoding="utf-8")
    (tmp_path / "sub" / ".config").mkdir()
    screen_all = FilePickerScreen(start_dir=tmp_path / "sub", show_all_files=True)
    screen_all._scan_directory()
    item_labels_all = [label for label, item_type, path in screen_all.items]
    assert any("doc2.markdown" in l for l in item_labels_all)
    assert any("ignored.txt" in l for l in item_labels_all)
    assert any(".vimrc" in l for l in item_labels_all)
    assert any(".config/" in l for l in item_labels_all)


def test_commander_screen(tmp_path: Path):
    from mdreader.widgets.commander import CommanderScreen, PaneWidget

    (tmp_path / "file1.md").write_text("# Hello", encoding="utf-8")
    (tmp_path / "script.py").write_text("print('test')", encoding="utf-8")
    (tmp_path / "folder").mkdir()

    pane = PaneWidget("test-pane", start_dir=tmp_path, show_all=True)
    pane.scan()
    items = pane.items
    assert any("file1.md" in i[0] for i in items)
    assert any("script.py" in i[0] for i in items)
    assert any("folder/" in i[0] for i in items)

    screen = CommanderScreen(current_path=tmp_path / "file1.md", show_all=True)
    assert screen.active_pane_id == "left-pane"
    screen.action_switch_pane()
    assert screen.active_pane_id == "right-pane"


def test_commander_modals():
    from mdreader.widgets.commander import PromptModal, ConfirmModal

    prompt = PromptModal(title="Test Prompt", initial_value="default_val")
    assert prompt.prompt_title == "Test Prompt"
    assert prompt.initial_value == "default_val"

    confirm = ConfirmModal(title="Delete Confirm", message="Delete file?")
    assert confirm.confirm_title == "Delete Confirm"
    assert confirm.confirm_msg == "Delete file?"


def test_commander_multiselect(tmp_path: Path):
    from mdreader.widgets.commander import PaneWidget

    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("a", encoding="utf-8")
    f2.write_text("b", encoding="utf-8")

    pane = PaneWidget("test-pane", start_dir=tmp_path, show_all=True)
    pane.scan()
    assert len(pane.selected_paths) == 0

    pane.selected_paths.add(f1)
    pane.selected_paths.add(f2)
    assert len(pane.get_effective_targets()) == 2

    pane.unselect_all_items()
    assert len(pane.selected_paths) == 0
