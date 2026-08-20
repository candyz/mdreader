"""Markdown viewer widget module."""
from textual.widgets import Markdown
from textual.containers import VerticalScroll
from mdreader.renderer.mermaid import preprocess_mermaid


class MarkdownViewerWidget(VerticalScroll):
    """Scrollable Markdown viewer widget with Mermaid preprocessing."""

    DEFAULT_CSS = """
    MarkdownViewerWidget {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    """

    def __init__(self, raw_markdown: str = "", max_width: int | None = None, **kwargs):
        super().__init__(**kwargs)
        self.raw_markdown = raw_markdown
        self.max_width = max_width
        self.markdown_widget = Markdown()

    def compose(self):
        yield self.markdown_widget

    def on_mount(self) -> None:
        self.update_content(self.raw_markdown)

    def update_content(self, markdown_text: str) -> None:
        """Process mermaid blocks and update the underlying Textual Markdown widget."""
        self.raw_markdown = markdown_text
        processed_md = preprocess_mermaid(markdown_text)
        self.markdown_widget.update(processed_md)
