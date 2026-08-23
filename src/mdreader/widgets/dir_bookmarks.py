"""Directory Bookmarks and Quick Jump modal dialog for mdreader."""
from __future__ import annotations
from pathlib import Path
from typing import Optional, List, Tuple
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import OptionList, Label, Button
from textual.widgets.option_list import Option
from textual.binding import Binding
from mdreader.utils.config import get_recent_files


class DirBookmarksModal(ModalScreen[Optional[Path]]):
    """Modal dialog for quick jumping to standard system and workspace directories."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
        Binding("enter", "select_item", "Select", priority=True),
    ]

    CSS = """
    DirBookmarksModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.75);
    }
    #bookmarks-dialog {
        width: 72;
        height: 22;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    #bookmarks-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        text-align: center;
    }
    #bookmarks-list {
        height: 1fr;
        background: $panel;
        border: solid $panel-darken-1;
        margin-bottom: 1;
    }
    #bookmarks-hint {
        color: $text-muted;
        text-style: italic;
        text-align: center;
    }
    """

    def __init__(self, current_dir: Path | None = None) -> None:
        super().__init__()
        self.current_dir = current_dir or Path.cwd()
        self.destinations: List[Tuple[str, Path]] = []
        self._populate_destinations()

    def _populate_destinations(self) -> None:
        home = Path.home()
        cwd = Path.cwd()
        dests: List[Tuple[str, Path]] = [
            (f"🏠 Home Directory ({home})", home),
            (f"📁 Workspace Root ({cwd})", cwd),
        ]

        downloads = home / "Downloads"
        if downloads.is_dir():
            dests.append((f"📥 Downloads ({downloads})", downloads))

        desktop = home / "Desktop"
        if desktop.is_dir():
            dests.append((f"🖥️ Desktop ({desktop})", desktop))

        documents = home / "Documents"
        if documents.is_dir():
            dests.append((f"📄 Documents ({documents})", documents))

        # Recent directories from recent files history
        recent_files = get_recent_files()
        seen_dirs = {home, cwd, downloads, desktop, documents}
        for rf in recent_files:
            rp = Path(rf).parent
            if rp.is_dir() and rp not in seen_dirs:
                seen_dirs.add(rp)
                dests.append((f"🕒 Recent: {rp.name} ({rp})", rp))
                if len(dests) >= 12:
                    break

        root = Path("/")
        dests.append((f"💻 Root Filesystem (/)", root))
        self.destinations = dests

    def compose(self) -> ComposeResult:
        with Vertical(id="bookmarks-dialog"):
            yield Label("🔖 Directory Bookmarks & Quick Jump", id="bookmarks-title")
            yield OptionList(id="bookmarks-list")
            yield Label("Enter: Select directory │ Esc: Cancel", id="bookmarks-hint")

    def on_mount(self) -> None:
        opt_list = self.query_one("#bookmarks-list", OptionList)
        for label, _ in self.destinations:
            opt_list.add_option(Option(prompt=label))
        opt_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        idx = event.option_index
        if 0 <= idx < len(self.destinations):
            self.dismiss(self.destinations[idx][1])
        else:
            self.dismiss(None)

    def action_select_item(self) -> None:
        opt_list = self.query_one("#bookmarks-list", OptionList)
        idx = opt_list.highlighted
        if idx is not None and 0 <= idx < len(self.destinations):
            self.dismiss(self.destinations[idx][1])
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
