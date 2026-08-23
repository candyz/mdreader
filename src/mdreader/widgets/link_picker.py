"""Link picker modal screen for searching and opening hyperlinks in default browser (gx)."""
from __future__ import annotations
import re
import webbrowser
from pathlib import Path
from typing import List, Tuple, Optional
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList, Label, Button
from textual.widgets.option_list import Option
from textual.binding import Binding
from mdreader.widgets.file_picker import fuzzy_score


def extract_links_from_text(text: str) -> List[Tuple[str, str]]:
    """Extract markdown [title](url) and raw http(s) links from text. Returns list of (label, url)."""
    links: List[Tuple[str, str]] = []
    seen_urls: set[str] = set()

    # 1. Markdown links [text](http://...)
    md_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)')
    for match in md_pattern.finditer(text):
        label = match.group(1).strip()
        url = match.group(2).strip()
        if url not in seen_urls:
            links.append((label, url))
            seen_urls.add(url)

    # 2. Raw URLs http(s)://...
    raw_pattern = re.compile(r'(https?://[^\s\)\]\>"\'`]+)')
    for match in raw_pattern.finditer(text):
        url = match.group(1).strip().rstrip(".,;:")
        if url not in seen_urls:
            links.append((url, url))
            seen_urls.add(url)

    return links


class LinkPickerModal(ModalScreen[Optional[str]]):
    """Modal dialog for filtering and opening hyperlinks found in document."""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Cancel", priority=True),
        Binding("tab", "dismiss_modal", "Cancel", priority=True),
        Binding("up", "move_up", "Up", priority=True, show=False),
        Binding("down", "move_down", "Down", priority=True, show=False),
    ]

    CSS = """
    LinkPickerModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.75);
    }
    #link-dialog {
        width: 80%;
        max-width: 90;
        height: 70%;
        background: $surface;
        border: thick $primary;
        padding: 0 1;
    }
    #link-title {
        height: 1;
        background: $primary-darken-2;
        color: $accent;
        text-style: bold;
        padding: 0 1;
    }
    #link-list {
        height: 1fr;
        background: $panel;
        border: solid $panel;
        margin: 0;
    }
    #link-filter {
        width: 100%;
        margin: 0;
    }
    #link-footer {
        height: 1;
        background: $footer-background;
        padding: 0 1;
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(self, links: List[Tuple[str, str]]):
        super().__init__()
        self.links = links

    def compose(self) -> ComposeResult:
        with Vertical(id="link-dialog"):
            yield Label(f"🔗 Document Hyperlinks ({len(self.links)} found)", id="link-title")
            yield OptionList(id="link-list")
            yield Input(placeholder="🔍 Filter hyperlinks... (Enter to open in browser, Esc to close)", id="link-filter")
            yield Label("💡 Enter: Open in browser | Up/Down: Navigate | Esc: Cancel", id="link-footer")

    def on_mount(self) -> None:
        self._refresh_list("")
        self.query_one("#link-filter", Input).focus()

    def _refresh_list(self, query: str = "") -> None:
        opt_list = self.query_one("#link-list", OptionList)
        opt_list.clear_options()

        q = query.strip()
        matched: List[Tuple[int, str, str]] = []
        for label, url in self.links:
            display_text = f"{label} → {url}" if label != url else url
            if not q:
                matched.append((0, display_text, url))
            else:
                is_m1, s1 = fuzzy_score(q, label)
                is_m2, s2 = fuzzy_score(q, url)
                if is_m1 or is_m2:
                    matched.append((max(s1, s2), display_text, url))

        if q:
            matched.sort(key=lambda x: x[0], reverse=True)

        for _, display_text, url in matched:
            opt_list.add_option(Option(prompt=f"🌐 {display_text}", id=url))

        if opt_list.option_count > 0:
            opt_list.highlighted = 0

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "link-filter":
            self._refresh_list(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        opt_list = self.query_one("#link-list", OptionList)
        if opt_list.highlighted is not None:
            opt = opt_list.get_option_at_index(opt_list.highlighted)
            if opt and opt.id:
                self._open_url(opt.id)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        if event.option.id:
            self._open_url(event.option.id)

    def _open_url(self, url: str) -> None:
        try:
            webbrowser.open(url)
        except Exception:
            pass
        self.dismiss(url)

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)

    def action_move_down(self) -> None:
        self.query_one("#link-list", OptionList).action_cursor_down()

    def action_move_up(self) -> None:
        self.query_one("#link-list", OptionList).action_cursor_up()
