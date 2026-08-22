"""Fuzzy Markdown & HTML File Picker modal / widget with directory navigation and all-files toggle."""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList, Label, Checkbox
from textual.widgets.option_list import Option
from textual.binding import Binding


class FilePickerScreen(ModalScreen[Optional[Path]]):
    """Maximized modal screen for browsing directories and selecting Markdown/HTML/Text files."""

    BINDINGS = [
        Binding("tab", "dismiss_modal", "Dismiss", priority=True),
        Binding("escape", "dismiss_modal", "Dismiss", priority=True),
        Binding("up", "move_up", "Up", priority=True, show=False),
        Binding("down", "move_down", "Down", priority=True, show=False),
        Binding("ctrl+a", "toggle_all_files", "Toggle All Files", priority=True),
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

    #picker-bottom-bar {
        height: auto;
        width: 100%;
        margin: 0;
        padding: 0;
    }

    #filter-input {
        width: 1fr;
        margin: 0;
    }

    #all-files-checkbox {
        width: auto;
        height: 1;
        margin: 0 1 0 1;
        background: transparent;
        border: none;
        padding: 0 1;
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

    def __init__(self, start_dir: Path | str = ".", initial_query: str = "", show_all_files: bool = False):
        super().__init__()
        self.current_dir = Path(start_dir).resolve()
        if not self.current_dir.is_dir():
            self.current_dir = self.current_dir.parent
        self.initial_query = initial_query
        self.show_all_files = show_all_files
        self.items: List[tuple[str, str, Path]] = []  # (display_label, type, path)

    def _scan_directory(self) -> None:
        """Scan current directory for parent dir (..), subdirectories, and files."""
        items: List[tuple[str, str, Path]] = []
        excluded_dirs = {".git", ".venv", "node_modules", "__pycache__", "dist", "build"}
        supported_exts = (".md", ".markdown", ".html", ".htm", ".xhtml")

        # 1. Add parent directory option if not root
        if self.current_dir.parent != self.current_dir:
            items.append(("📁 .. (Parent Directory)", "parent_dir", self.current_dir.parent))

        # 2. Add subdirectories & files
        try:
            subdirs = []
            files = []
            for entry in self.current_dir.iterdir():
                # If not showing all files, skip hidden files and directories
                if not self.show_all_files and entry.name.startswith(".") and entry.name != "..":
                    continue
                if entry.is_dir():
                    if entry.name not in excluded_dirs:
                        subdirs.append(entry)
                elif entry.is_file():
                    ext = entry.name.lower()
                    if self.show_all_files:
                        files.append(entry)
                    else:
                        if ext.endswith(supported_exts):
                            files.append(entry)

            for d in sorted(subdirs, key=lambda p: p.name.lower()):
                items.append((f"📁 {d.name}/", "dir", d))

            for f in sorted(files, key=lambda p: p.name.lower()):
                fname_lower = f.name.lower()
                if fname_lower.endswith((".html", ".htm", ".xhtml")):
                    ext_icon = "🌐"
                elif fname_lower.endswith((".md", ".markdown")):
                    ext_icon = "📄"
                elif fname_lower.endswith((".py", ".sh", ".bash", ".zsh", ".js", ".ts", ".json", ".toml", ".yaml", ".yml", ".c", ".cpp", ".rs", ".go")):
                    ext_icon = "📜"
                else:
                    ext_icon = "📝"
                items.append((f"{ext_icon} {f.name}", "file", f))

        except Exception as e:
            items.append((f"⚠️ Error reading directory: {e}", "error", self.current_dir))

        self.items = items

    def compose(self) -> ComposeResult:
        with Vertical(id="picker-dialog"):
            with Horizontal(id="picker-header"):
                yield Label(f"📂 {self.current_dir}", id="picker-title")
            yield OptionList(id="file-list")
            with Horizontal(id="picker-bottom-bar"):
                yield Input(
                    value=self.initial_query,
                    placeholder="🔍 Filter files/folders... (↑/↓: navigate, Enter: select/enter, Esc: cancel)",
                    id="filter-input",
                )
                yield Checkbox("Show all files (Ctrl+A)", value=self.show_all_files, id="all-files-checkbox")
            with Horizontal(id="picker-footer"):
                yield Label("💡 Enter: Open file / Enter folder | Ctrl+A: Toggle all files | Tab/Esc: Close", id="picker-hint")

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
                filtered.append((label, item_type, path))
            elif not q or q in label.lower() or q in path.name.lower():
                filtered.append((label, item_type, path))

        for label, item_type, path in filtered:
            option_list.add_option(Option(prompt=label, id=f"{item_type}:{path}"))

        if option_list.option_count > 0:
            option_list.highlighted = 0

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "all-files-checkbox":
            self.show_all_files = event.value
            filter_input = self.query_one("#filter-input", Input)
            self._refresh_view(filter_input.value)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "filter-input":
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
            self.current_dir = target_path.resolve()
            filter_input = self.query_one("#filter-input", Input)
            filter_input.value = ""
            self._refresh_view()
            filter_input.focus()
        elif item_type == "file":
            self.dismiss(target_path)

    def action_toggle_all_files(self) -> None:
        """Toggle Show All Files checkbox via Ctrl+A."""
        cb = self.query_one("#all-files-checkbox", Checkbox)
        cb.value = not cb.value

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
