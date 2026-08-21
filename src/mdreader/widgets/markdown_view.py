"""Markdown viewer widget module with Mermaid preprocessing & TOC support."""
from textual.widgets import MarkdownViewer
from mdreader.renderer.mermaid import preprocess_mermaid


class MarkdownViewerWidget(MarkdownViewer):
    """Integrated Markdown viewer widget with Mermaid preprocessing and TOC support."""

    DEFAULT_CSS = """
    MarkdownViewerWidget {
        width: 100%;
        height: 100%;
    }
    """

    def __init__(
        self,
        raw_markdown: str = "",
        show_toc: bool = False,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        self.raw_markdown = raw_markdown
        processed_md = preprocess_mermaid(raw_markdown) if raw_markdown else ""
        super().__init__(
            markdown=processed_md,
            show_table_of_contents=show_toc,
            name=name,
            id=id,
            classes=classes,
        )

    def update_content(self, markdown_text: str) -> None:
        """Process mermaid blocks and update the document."""
        self.raw_markdown = markdown_text
        processed_md = preprocess_mermaid(markdown_text)
        self.document.update(processed_md)

    def toggle_toc(self) -> None:
        """Toggle Table of Contents sidebar visibility."""
        self.show_table_of_contents = not self.show_table_of_contents

    def scroll_relative_custom(self, dy: int) -> None:
        """Scroll document up or down."""
        self.scroll_relative(y=dy)

    def page_down(self) -> None:
        """Scroll down by one page."""
        self.action_page_down()

    def page_up(self) -> None:
        """Scroll up by one page."""
        self.action_page_up()

    def scroll_home(self) -> None:
        """Scroll to the top of the document (gg / Home)."""
        self.action_scroll_home()

    def scroll_end(self) -> None:
        """Scroll to the bottom of the document (G / End)."""
        self.action_scroll_end()
