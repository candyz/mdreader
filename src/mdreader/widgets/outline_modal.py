"""Outline / Table of Contents Modal Screen."""
from typing import List, Tuple
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import OptionList, Label, Input
from textual.widgets.option_list import Option


class OutlineModalScreen(ModalScreen[str | None]):
    """Modal screen displaying document outline (TOC) with quick navigation and search."""

    CSS = """
    OutlineModalScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.75);
    }

    #outline-dialog {
        width: 85%;
        height: 85%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #outline-header {
        height: auto;
        margin-bottom: 1;
    }

    #outline-title {
        text-style: bold;
        color: $accent;
    }

    #outline-filter {
        margin-bottom: 1;
    }

    #outline-list {
        height: 1fr;
        border: solid $panel;
        background: $panel;
    }

    #outline-footer {
        height: auto;
        margin-top: 1;
        align: right middle;
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
            yield Input(
                placeholder="過濾章節名稱... (↑/↓/j/k 移動, Enter 跳轉, Tab/Esc 返回文章)",
                id="outline-filter",
            )
            yield OptionList(id="outline-list")
            with Horizontal(id="outline-footer"):
                yield Label("按 Enter 跳轉至該章節 | 按 Tab 或 Esc 返回文章", id="outline-hint")

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

    def key_escape(self) -> None:
        self.dismiss(None)

    def key_tab(self) -> None:
        self.dismiss(None)

    def key_down(self) -> None:
        self.query_one("#outline-list", OptionList).action_cursor_down()

    def key_up(self) -> None:
        self.query_one("#outline-list", OptionList).action_cursor_up()
