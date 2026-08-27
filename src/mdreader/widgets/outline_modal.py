"""Outline / Table of Contents Modal Screen."""
from __future__ import annotations
from typing import List, Tuple, Optional
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import OptionList, Label, Input
from textual.widgets.option_list import Option


from textual.binding import Binding


class OutlineModalScreen(ModalScreen[Optional[str]]):
    """Full-screen modal displaying document outline (TOC) with quick navigation and bottom search."""

    BINDINGS = [
        Binding("tab", "dismiss_modal", "Dismiss", priority=True),
        Binding("escape", "dismiss_modal", "Dismiss", priority=True),
        Binding("up", "move_up", "Up", priority=True, show=False),
        Binding("down", "move_down", "Down", priority=True, show=False),
    ]

    CSS = """
    OutlineModalScreen {
        background: $surface;
        layout: vertical;
    }

    #outline-dialog {
        width: 100%;
        height: 100%;
        background: $surface;
        border: none;
        padding: 0;
    }

    #outline-header {
        height: 1;
        width: 100%;
        margin: 0;
        background: $primary-darken-2;
        padding: 0 1;
    }

    #outline-title {
        text-style: bold;
        color: $accent;
        width: 1fr;
    }

    #outline-list {
        height: 1fr;
        border: none;
        background: $panel;
        margin: 0;
    }

    #outline-bottom-bar {
        height: 1;
        width: 100%;
        margin: 0;
        padding: 0 1;
        background: $surface-darken-1;
    }

    #outline-filter {
        width: 100%;
        height: 1;
        border: none;
        padding: 0;
        background: transparent;
        color: $text;
    }

    #outline-footer {
        height: 1;
        width: 100%;
        margin: 0;
        background: $footer-background;
        padding: 0 1;
    }

    #outline-hint {
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(self, headings: List[Tuple[int, str, str]]):
        """Initialize outline modal with list of (level, title, block_id)."""
        super().__init__()
        self.headings = headings

    def compose(self) -> ComposeResult:
        with Vertical(id="outline-dialog"):
            with Horizontal(id="outline-header"):
                yield Label("📑 大綱模式 (Outline) — 選擇章節跳轉", id="outline-title")
            yield OptionList(id="outline-list")
            with Horizontal(id="outline-bottom-bar"):
                yield Input(
                    placeholder="🔍 過濾章節名稱... (↑/↓ 移動, Enter 跳轉, Tab/Esc 返回文章)",
                    id="outline-filter",
                )
            with Horizontal(id="outline-footer"):
                yield Label("💡 Enter: 跳轉至該章節 | ↑/↓: 移動選取 | Tab/Esc: 返回文章", id="outline-hint")

    def on_mount(self) -> None:
        self._update_list("")
        self.query_one("#outline-filter", Input).focus()

    def _update_list(self, filter_text: str) -> None:
        option_list = self.query_one("#outline-list", OptionList)
        option_list.clear_options()

        q = filter_text.lower().strip()
        for level, title, block_id in self.headings:
            if not q or q in title.lower():
                # Indent based on heading level
                indent = "  " * (level - 1)
                prefix = "#" * level
                prompt = f"{indent}{prefix} {title}"
                option_list.add_option(Option(prompt=prompt, id=block_id))

    def on_input_changed(self, event: Input.Changed) -> None:
        self._update_list(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        option_list = self.query_one("#outline-list", OptionList)
        if option_list.highlighted is not None:
            option = option_list.get_option_at_index(option_list.highlighted)
            if option and option.id:
                self.dismiss(option.id)
                return
        if option_list.option_count > 0:
            option = option_list.get_option_at_index(0)
            if option and option.id:
                self.dismiss(option.id)
                return
        self.dismiss(None)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        if event.option.id:
            self.dismiss(event.option.id)

    def on_key(self, event) -> None:
        """Handle raw key events to ensure immediate response to tab and escape."""
        if event.key in ("tab", "escape"):
            event.stop()
            event.prevent_default()
            self.dismiss(None)

    def action_dismiss_modal(self) -> None:
        """Dismiss outline modal without selection."""
        self.dismiss(None)

    def action_move_down(self) -> None:
        """Move cursor down in outline list."""
        self.query_one("#outline-list", OptionList).action_cursor_down()

    def action_move_up(self) -> None:
        """Move cursor up in outline list."""
        self.query_one("#outline-list", OptionList).action_cursor_up()
