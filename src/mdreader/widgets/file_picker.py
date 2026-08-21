"""Fuzzy Markdown & HTML File Picker modal / widget with directory navigation."""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList, Label
from textual.widgets.option_list import Option
from textual.binding import Binding


class FilePickerScreen(ModalScreen[Optional[Path]]):
    """Maximized modal screen for browsing directories and selecting Markdown/HTML files."""

    BINDINGS = [
        Binding("tab", "dismiss_modal", "Dismiss", priority=True),
        Binding("escape", "dismiss_modal", "Dismiss", priority=True),
        Binding("up", "move_up", "Up", priority=True, show=False),
        Binding("down", "move_down", "Down", priority=True, show=False),
    ]

    CSS = """
    FilePickerScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.75);
    }

    #picker-dialog {
        width: 96%;
        height: 94%;
        background: $surface;
        border: thick $primary;
        padding: 0 1;
    }

    #picker-header {
        height: 1;
        width: 100%;
        margin-top: 0;
        margin-bottom: 0;
        background: $primary-darken-2;
        padding: 0 1;
    }

    #picker-title {
        text-style: bold;
        color: $accent;
        width: 1fr;
    }

    #file-list {
        height: 1fr;
        border: solid $panel;
        background: $panel;
        margin: 0;
    }

    #filter-container {
        height: auto;
        margin-top: 0;
        margin-bottom: 0;
    }

    #filter-input {
        width: 100%;
        margin: 0;
    }

    #picker-footer {
        height: 1;
        width: 100%;
        margin-top: 0;
        background: $footer-background;
        padding: 0 1;
    }

    #picker-hint {
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(self, start_dir: Path | str = ".", initial_query: str = ""):
        super().__init__()
        self.current_dir = Path(start_dir).resolve()
        if not self.current_dir.is_dir():
            self.current_dir = self.current_dir.parent
        self.initial_query = initial_query
        self.items: List[tuple[str, str, Path]] = []  # (display_label, type, path)

    def _scan_directory(self) -> None:
        """Scan current directory for parent dir (..), subdirectories, and markdown/html files."""
        items: List[tuple[str, str, Path]] = []
        excluded_dirs = {".git", ".venv", "node_modules", "__pycache__", "dist", "build"}
        supported_exts = (".md", ".markdown", ".html", ".htm", ".xhtml")

        # 1. Add parent directory option if not root
        if self.current_dir.parent != self.current_dir:
            items.append(("📁 .. (Parent Directory)", "parent_dir", self.current_dir.parent))

        # 2. Add subdirectories
        try:
            subdirs = []
            files = []
            for entry in self.current_dir.iterdir():
                if entry.name.startswith(".") and entry.name != "..":
                    continue
                if entry.is_dir():
                    if entry.name not in excluded_dirs:
                        subdirs.append(entry)
                elif entry.is_file():
                    if entry.name.lower().endswith(supported_exts):
                        files.append(entry)

            for d in sorted(subdirs, key=lambda p: p.name.lower()):
                items.append((f"📁 {d.name}/", "dir", d))

            for f in sorted(files, key=lambda p: p.name.lower()):
                ext_icon = "🌐" if f.name.lower().endswith((".html", ".htm", ".xhtml")) else "📄"
                items.append((f"{ext_icon} {f.name}", "file", f))

        except Exception as e:
            items.append((f"⚠️ Error reading directory: {e}", "error", self.current_dir))

        self.items = items

    def compose(self) -> ComposeResult:
        with Vertical(id="picker-dialog"):
            with Horizontal(id="picker-header"):
                yield Label(f"📂 {self.current_dir}", id="picker-title")
            yield OptionList(id="file-list")
            with Vertical(id="filter-container"):
                yield Input(
                    value=self.initial_query,
                    placeholder="🔍 Filter files/folders... (↑/↓ to navigate, Enter to open/enter, Esc to cancel)",
                    id="filter-input",
                )
            with Horizontal(id="picker-footer"):
                yield Label("💡 Enter: Open file / Enter directory | Tab / Esc: Close", id="picker-hint")

    def on_mount(self) -> None:
        self._refresh_view(self.initial_query)
        self.query_one("#filter-input", Input).focus()

    def _refresh_view(self, query: str = "") -> None:
        self._scan_directory()
        title_label = self.query_one("#picker-title", Label)
        title_label.update(f"📂 {self.current_dir}")

        option_list = self.query_one("#file-list", OptionList)
        option_list.clear_options()

        q = query.lower().strip()
        filtered: List[tuple[str, str, Path]] = []
        for label, item_type, path in self.items:
            if item_type == "parent_dir":
                # Always keep parent dir visible unless query is specific and doesn't match
                filtered.append((label, item_type, path))
            elif not q or q in label.lower() or q in path.name.lower():
                filtered.append((label, item_type, path))

        for idx, (label, item_type, path) in enumerate(filtered):
            option_list.add_option(Option(prompt=label, id=f"{item_type}:{path}"))

        if option_list.option_count > 0:
            option_list.highlighted = 0

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "filter-input":
            # Re-filter current items
            option_list = self.query_one("#file-list", OptionList)
            option_list.clear_options()

            q = event.value.lower().strip()
            for label, item_type, path in self.items:
                if item_type == "parent_dir":
                    if not q or ".." in q or "parent" in q:
                        option_list.add_option(Option(prompt=label, id=f"{item_type}:{path}"))
                elif not q or q in label.lower() or q in path.name.lower():
                    option_list.add_option(Option(prompt=label, id=f"{item_type}:{path}"))

            if option_list.option_count > 0:
                option_list.highlighted = 0

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        option_list = self.query_one("#file-list", OptionList)
        selected_opt = None
        if option_list.highlighted is not None:
            selected_opt = option_list.get_option_at_index(option_list.highlighted)
        elif option_list.option_count > 0:
            selected_opt = option_list.get_option_at_index(0)

        if selected_opt and selected_opt.id:
            self._handle_selection(selected_opt.id)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        if event.option.id:
            self._handle_selection(event.option.id)

    def _handle_selection(self, option_id: str) -> None:
        """Handle selection of parent directory, subfolder, or file."""
        if ":" not in option_id:
            return
        item_type, path_str = option_id.split(":", 1)
        target_path = Path(path_str)

        if item_type in ("parent_dir", "dir"):
            # Navigate into directory
            self.current_dir = target_path.resolve()
            filter_input = self.query_one("#filter-input", Input)
            filter_input.value = ""
            self._refresh_view()
            filter_input.focus()
        elif item_type == "file":
            # Return selected file to caller
            self.dismiss(target_path)

    def on_key(self, event) -> None:
        """Handle key events for tab and escape dismissal."""
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
