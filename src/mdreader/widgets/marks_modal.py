"""Marks & Bookmarks modal screen for viewing and jumping to set marks in mdreader."""
from __future__ import annotations
from typing import Dict, Optional, Tuple, List
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import OptionList, Label, Button
from textual.widgets.option_list import Option
from textual.binding import Binding


class MarksModal(ModalScreen[Optional[int]]):
    """Modal screen displaying all currently set bookmarks (marks)."""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Cancel", priority=True),
        Binding("tab", "dismiss_modal", "Cancel", priority=True),
        Binding("up", "move_up", "Up", priority=True, show=False),
        Binding("down", "move_down", "Down", priority=True, show=False),
    ]

    CSS = """
    MarksModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.75);
    }
    #marks-dialog {
        width: 60;
        height: auto;
        max-height: 20;
        background: $surface;
        border: thick $primary;
        padding: 0 1;
    }
    #marks-title {
        height: 1;
        background: $primary-darken-2;
        color: $accent;
        text-style: bold;
        padding: 0 1;
    }
    #marks-list {
        height: auto;
        max-height: 14;
        background: $panel;
        border: solid $panel;
        margin: 0;
    }
    #marks-footer {
        height: 1;
        background: $footer-background;
        padding: 0 1;
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(self, marks: Dict[str, int], lines: List[str] | None = None):
        super().__init__()
        self.marks = marks
        self.lines = lines or []

    def compose(self) -> ComposeResult:
        with Vertical(id="marks-dialog"):
            yield Label(f"🔖 Bookmarks / Marks ({len(self.marks)} set)", id="marks-title")
            yield OptionList(id="marks-list")
            yield Label("💡 Enter: Jump to mark | 'a-'z: Quick jump | Esc: Cancel", id="marks-footer")

    def on_mount(self) -> None:
        opt_list = self.query_one("#marks-list", OptionList)
        if not self.marks:
            opt_list.add_option(Option(prompt="ℹ️ No bookmarks set yet. Press 'm' followed by a letter to set a mark.", id="none"))
        else:
            for key in sorted(self.marks.keys()):
                line_no = self.marks[key]
                preview = ""
                if 1 <= line_no <= len(self.lines):
                    preview = f" │ {self.lines[line_no - 1].strip()[:35]}"
                opt_list.add_option(Option(prompt=f"🔖 [{key.upper()}] Line {line_no:<5}{preview}", id=str(line_no)))

        if opt_list.option_count > 0:
            opt_list.highlighted = 0
        opt_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        if event.option.id and event.option.id.isdigit():
            self.dismiss(int(event.option.id))
        else:
            self.dismiss(None)

    def on_key(self, event) -> None:
        if event.character and event.character.lower() in self.marks:
            event.stop()
            self.dismiss(self.marks[event.character.lower()])

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)

    def action_move_down(self) -> None:
        self.query_one("#marks-list", OptionList).action_cursor_down()

    def action_move_up(self) -> None:
        self.query_one("#marks-list", OptionList).action_cursor_up()
