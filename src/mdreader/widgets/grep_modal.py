"""Directory Content Grep Search modal for mdreader."""
from __future__ import annotations
from pathlib import Path
from typing import Optional, List, Tuple
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList, Label
from textual.widgets.option_list import Option
from textual.binding import Binding
from mdreader.utils.grep import grep_search


class GrepSearchModal(ModalScreen[Optional[Tuple[Path, int]]]):
    """Modal dialog for searching text content inside files in the current directory."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
        Binding("up", "move_up", "Up", priority=True, show=False),
        Binding("down", "move_down", "Down", priority=True, show=False),
    ]

    CSS = """
    GrepSearchModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.75);
    }
    #grep-dialog {
        width: 90%;
        height: 85%;
        background: $surface;
        border: thick $primary;
        padding: 0 1;
    }
    #grep-title {
        text-style: bold;
        color: $accent;
        margin-top: 1;
        margin-bottom: 1;
        text-align: center;
    }
    #grep-input {
        width: 100%;
        margin-bottom: 1;
    }
    #grep-list {
        height: 1fr;
        background: $panel;
        border: solid $panel-darken-1;
        margin-bottom: 1;
    }
    #grep-footer {
        height: 1;
        background: $footer-background;
        padding: 0 1;
    }
    #grep-hint {
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(self, root_dir: Path | str = ".") -> None:
        super().__init__()
        self.root_dir = Path(root_dir).resolve()
        self.matches: List[Tuple[Path, int, str]] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="grep-dialog"):
            yield Label(f"🔍 Search File Contents in: {self.root_dir}", id="grep-title")
            yield Input(placeholder="Type keyword and press Enter to search...", id="grep-input")
            yield OptionList(id="grep-list")
            with Horizontal(id="grep-footer"):
                yield Label("Enter: Search / Open file at line │ Up/Down: Navigate │ Esc: Back", id="grep-hint")

    def on_mount(self) -> None:
        self.query_one("#grep-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        opt_list = self.query_one("#grep-list", OptionList)
        opt_list.clear_options()

        if not query:
            return

        self.matches = grep_search(self.root_dir, query, max_results=80)
        if not self.matches:
            opt_list.add_option(Option(prompt=f"❌ No matches found for '{query}' in {self.root_dir.name}"))
            return

        for path, line_no, content in self.matches:
            rel_path = path.name
            try:
                rel_path = str(path.relative_to(self.root_dir))
            except ValueError:
                pass
            preview = content[:80]
            label = f"[bold cyan]{rel_path}:{line_no}[/]  [dim]{preview}[/]"
            opt_list.add_option(Option(prompt=label))

        opt_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        idx = event.option_index
        if 0 <= idx < len(self.matches):
            path, line_no, _ = self.matches[idx]
            self.dismiss((path, line_no))
        else:
            self.dismiss(None)

    def action_move_up(self) -> None:
        opt_list = self.query_one("#grep-list", OptionList)
        opt_list.action_cursor_up()

    def action_move_down(self) -> None:
        opt_list = self.query_one("#grep-list", OptionList)
        opt_list.action_cursor_down()

    def action_cancel(self) -> None:
        self.dismiss(None)
