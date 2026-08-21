"""Markdown viewer widget module with Mermaid preprocessing & TOC support."""
from textual.widgets import MarkdownViewer
from textual.containers import VerticalScroll
from mdreader.renderer.mermaid import preprocess_mermaid


class MarkdownViewerWidget(VerticalScroll):
    """Scrollable Markdown viewer widget with Mermaid preprocessing."""

    DEFAULT_CSS = """
    MarkdownViewerWidget {
        width: 100%;
        height: 100%;
    }

    MarkdownViewerWidget > MarkdownViewer {
        width: 100%;
        height: 100%;
    }
    """

    def __init__(
        self,
        raw_markdown: str = "",
        show_toc: bool = True,
        max_width: int | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.raw_markdown = raw_markdown
        self.show_toc = show_toc
        self.max_width = max_width
        processed_md = preprocess_mermaid(raw_markdown) if raw_markdown else ""
        self.viewer = MarkdownViewer(
            markdown=processed_md,
            show_table_of_contents=show_toc,
        )

    def compose(self):
        yield self.viewer

    def update_content(self, markdown_text: str) -> None:
        """Process mermaid blocks and update the underlying MarkdownViewer."""
        self.raw_markdown = markdown_text
        processed_md = preprocess_mermaid(markdown_text)
        self.viewer.document.update(processed_md)

    def toggle_toc(self) -> None:
        """Toggle Table of Contents sidebar visibility."""
        self.viewer.show_table_of_contents = not self.viewer.show_table_of_contents

    def scroll_relative_custom(self, dy: int) -> None:
        """Scroll document up or down."""
        self.viewer.scroll_relative(y=dy)

    def page_down(self) -> None:
        """Scroll down by one page."""
        self.viewer.action_page_down()

    def page_up(self) -> None:
        """Scroll up by one page."""
        self.viewer.action_page_up()
