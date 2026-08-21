"""Fuzzy Markdown File Picker modal / widget."""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList, Label, Button
from textual.widgets.option_list import Option
from textual.binding import Binding


class FilePickerScreen(ModalScreen[Optional[Path]]):
    """Modal screen for fuzzy searching and picking markdown files in current directory tree."""

    BINDINGS = [
        Binding("tab", "dismiss_modal", "Dismiss", priority=True),
        Binding("escape", "dismiss_modal", "Dismiss", priority=True),
        Binding("up", "move_up", "Up", priority=True, show=False),
        Binding("down", "move_down", "Down", priority=True, show=False),
    ]

    CSS = """
    FilePickerScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #picker-dialog {
        width: 80%;
        height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #picker-header {
        height: auto;
        margin-bottom: 1;
    }

    #picker-title {
        text-style: bold;
        color: $accent;
    }

    #filter-input {
        margin-bottom: 1;
    }

    #file-list {
        height: 1fr;
        border: solid $panel;
        background: $panel;
    }

    #picker-footer {
        height: auto;
        margin-top: 1;
        align: right middle;
    }
    """

    def __init__(self, start_dir: Path | str = ".", initial_query: str = ""):
        super().__init__()
        self.start_dir = Path(start_dir).resolve()
        self.initial_query = initial_query
        self.all_files: List[Path] = []
        self._scan_markdown_files()

    def _scan_markdown_files(self) -> None:
        """Scan current directory recursively for .md files (excluding hidden/venv dirs)."""
        excluded_dirs = {".git", ".venv", "node_modules", "__pycache__", "dist", "build"}
        files = []
        try:
            for root, dirs, filenames in self.start_dir.walk():
                # Filter out excluded directories in-place
                dirs[:] = [d for d in dirs if d not in excluded_dirs and not d.startswith(".")]
                for fname in filenames:
                    if fname.endswith((".md", ".markdown")):
                        full_path = root / fname
                        files.append(full_path)
        except Exception:
            # Fallback to rglob if walk not supported on older python
            for p in self.start_dir.rglob("*.md"):
                if not any(part in excluded_dirs or part.startswith(".") for part in p.parts):
                    files.append(p)

        self.all_files = sorted(files, key=lambda p: p.name.lower())

    def compose(self) -> ComposeResult:
        with Vertical(id="picker-dialog"):
            with Horizontal(id="picker-header"):
                yield Label("📂 Select a Markdown File to Open", id="picker-title")
            yield Input(
                value=self.initial_query,
                placeholder="Type to filter files by name... (↑/↓ to navigate, Enter to select, Esc to cancel)",
                id="filter-input",
            )
            yield OptionList(id="file-list")
            with Horizontal(id="picker-footer"):
                yield Label("Press Esc to Cancel | Enter to Open", id="picker-hint")

    def on_mount(self) -> None:
        self._update_file_list(self.initial_query)
        self.query_one("#filter-input", Input).focus()

    def _update_file_list(self, query: str) -> None:
        option_list = self.query_one("#file-list", OptionList)
        option_list.clear_options()

        q = query.lower().strip()
        matched = []
        for path in self.all_files:
            try:
                rel = path.relative_to(self.start_dir)
            except ValueError:
                rel = path
            rel_str = str(rel)
            if not q or q in rel_str.lower():
                matched.append((rel_str, path))

        for rel_str, path in matched:
            option_list.add_option(Option(prompt=rel_str, id=str(path)))

    def on_input_changed(self, event: Input.Changed) -> None:
        self._update_file_list(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        option_list = self.query_one("#file-list", OptionList)
        if option_list.highlighted is not None:
            option = option_list.get_option_at_index(option_list.highlighted)
            if option and option.id:
                self.dismiss(Path(option.id))
                return
        # If nothing highlighted, pick first option
        if option_list.option_count > 0:
            option = option_list.get_option_at_index(0)
            if option and option.id:
                self.dismiss(Path(option.id))
                return
        self.dismiss(None)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        if event.option.id:
            self.dismiss(Path(event.option.id))

    def on_key(self, event) -> None:
        """Handle raw key events to ensure immediate response to tab and escape."""
        if event.key in ("tab", "escape"):
            event.stop()
            event.prevent_default()
            self.dismiss(None)

    def action_dismiss_modal(self) -> None:
        """Dismiss file picker modal."""
        self.dismiss(None)

    def action_move_down(self) -> None:
        """Move down in file list."""
        self.query_one("#file-list", OptionList).action_cursor_down()

    def action_move_up(self) -> None:
        """Move up in file list."""
        self.query_one("#file-list", OptionList).action_cursor_up()
