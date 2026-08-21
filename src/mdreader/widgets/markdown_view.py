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

    def scroll_horizontal(self, dx: int) -> None:
        """Scroll wide elements (such as code fences) horizontally."""
        # 1. First scroll viewer itself if it supports horizontal scrolling
        if self.allow_horizontal_scroll and self.max_scroll_x > 0:
            self.scroll_relative(x=dx)
        
        # 2. Scroll any visible code block / scrollable child in the current viewport
        from textual.widgets._markdown import MarkdownFence
        for child in self.document.children:
            if isinstance(child, MarkdownFence) and child.max_scroll_x > 0:
                child.scroll_to(x=max(0, min(child.max_scroll_x, child.scroll_x + dx)), animate=True)

    def page_down(self) -> None:
        """Scroll down by one page."""
        self.action_page_down()

    def page_up(self) -> None:
        """Scroll up by one page."""
        self.action_page_up()

    def get_headings(self) -> list[tuple[int, str, str]]:
        """Extract all markdown headings as (level, title, block_id)."""
        headings = []
        for block in self.document.children:
            type_name = type(block).__name__
            if type_name.startswith("MarkdownH"):
                try:
                    level = int(type_name.replace("MarkdownH", ""))
                except ValueError:
                    level = 1
                
                title = ""
                if hasattr(block, "_inline_token") and block._inline_token and block._inline_token.content:
                    title = block._inline_token.content
                elif hasattr(block, "_content"):
                    title = str(block._content)
                else:
                    title = str(block)
                
                block_id = block.id or ""
                if title.strip() and block_id:
                    headings.append((level, title.strip(), block_id))
        return headings

    def scroll_to_heading_id(self, block_id: str) -> None:
        """Scroll document directly to the heading block matching block_id."""
        from textual.widgets._markdown import MarkdownBlock
        try:
            block = self.document.query_one(f"#{block_id}", MarkdownBlock)
            self.scroll_to_widget(block, top=True)
        except Exception:
            pass
