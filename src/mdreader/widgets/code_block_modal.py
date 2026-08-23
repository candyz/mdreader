"""Modal dialog for listing, previewing, and copying code blocks from markdown."""
from __future__ import annotations
import re
from typing import Optional, List, Tuple
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import OptionList, Label
from textual.widgets.option_list import Option
from textual.binding import Binding


def extract_code_blocks(markdown_text: str) -> List[Tuple[str, str]]:
    """Extract fenced code blocks returning list of (language, code_content)."""
    if not markdown_text:
        return []
    pattern = re.compile(r"```([a-zA-Z0-9_\+\-\#]*)\n(.*?)```", re.DOTALL)
    blocks: List[Tuple[str, str]] = []
    for match in pattern.finditer(markdown_text):
        lang = match.group(1).strip() or "code"
        code = match.group(2).rstrip("\r\n")
        if code.strip():
            blocks.append((lang, code))
    return blocks


class CodeBlockModal(ModalScreen[Optional[str]]):
    """Modal dialog for browsing and copying code blocks."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
        Binding("up", "move_up", "Up", priority=True, show=False),
        Binding("down", "move_down", "Down", priority=True, show=False),
    ]

    CSS = """
    CodeBlockModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.75);
    }
    #blocks-dialog {
        width: 86%;
        height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 0 1;
    }
    #blocks-title {
        text-style: bold;
        color: $accent;
        margin-top: 1;
        margin-bottom: 1;
        text-align: center;
    }
    #blocks-list {
        height: 1fr;
        background: $panel;
        border: solid $panel-darken-1;
        margin-bottom: 1;
    }
    #blocks-hint {
        color: $text-muted;
        text-style: italic;
        padding: 0 1;
    }
    """

    def __init__(self, code_blocks: List[Tuple[str, str]]) -> None:
        super().__init__()
        self.code_blocks = code_blocks

    def compose(self) -> ComposeResult:
        with Vertical(id="blocks-dialog"):
            yield Label(f"💻 Select Code Block to Copy ({len(self.code_blocks)} blocks)", id="blocks-title")
            yield OptionList(id="blocks-list")
            yield Label("Enter: Copy selected code to clipboard │ Up/Down: Navigate │ Esc: Cancel", id="blocks-hint")

    def on_mount(self) -> None:
        opt_list = self.query_one("#blocks-list", OptionList)
        for idx, (lang, code) in enumerate(self.code_blocks):
            lines = code.splitlines()
            first_line = lines[0].strip() if lines else ""
            line_count = len(lines)
            prompt = f"[{idx+1}] [bold green]<{lang}>[/] ({line_count} lines)  [dim]{first_line[:60]}[/]"
            opt_list.add_option(Option(prompt=prompt))
        opt_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        idx = event.option_index
        if 0 <= idx < len(self.code_blocks):
            self.dismiss(self.code_blocks[idx][1])
        else:
            self.dismiss(None)

    def action_move_up(self) -> None:
        self.query_one("#blocks-list", OptionList).action_cursor_up()

    def action_move_down(self) -> None:
        self.query_one("#blocks-list", OptionList).action_cursor_down()

    def action_cancel(self) -> None:
        self.dismiss(None)
