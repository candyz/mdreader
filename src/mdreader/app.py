"""Textual Application for Markdown Reader."""
from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer
from textual.containers import Container
from mdreader.widgets.markdown_view import MarkdownViewerWidget


class MDReaderApp(App):
    """Interactive TUI Markdown Reader Application."""

    TITLE = "mdreader"
    SUB_TITLE = "Terminal Markdown Viewer"

    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #reader-box {
        width: 100%;
        height: 100%;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("escape", "quit", "Quit", show=False),
        Binding("j", "scroll_down", "Down", show=False),
        Binding("k", "scroll_up", "Up", show=False),
    ]

    def __init__(
        self,
        content: str = "",
        filepath: Path | str | None = None,
        max_width: int | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.content = content
        self.filepath = Path(filepath) if filepath else None
        self.max_width = max_width

        if self.filepath:
            self.SUB_TITLE = str(self.filepath.name)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            with Container(id="reader-box"):
                yield MarkdownViewerWidget(
                    raw_markdown=self.content,
                    max_width=self.max_width,
                    id="viewer",
                )
        yield Footer()

    def on_mount(self) -> None:
        if self.max_width:
            reader_box = self.query_one("#reader-box")
            reader_box.styles.max_width = self.max_width

    def action_scroll_down(self) -> None:
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        viewer.scroll_relative(y=3)

    def action_scroll_up(self) -> None:
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        viewer.scroll_relative(y=-3)
