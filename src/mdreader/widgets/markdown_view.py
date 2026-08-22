"""Markdown viewer widget module with Mermaid preprocessing & TOC support."""
from __future__ import annotations
import textual.widgets._markdown as tm
from textual.widgets import MarkdownViewer
from textual.widgets._markdown import MarkdownTable, MarkdownTableContent, MarkdownFence
from textual.css.scalar import Scalar
from rich.cells import cell_len
from mdreader.renderer.mermaid import preprocess_mermaid
from mdreader.renderer.html import html_to_markdown, is_html_content, is_markdown_file


# Monkey-patch Textual's MarkdownTable.compose so each column width is computed
# from the maximum length among the header and all rows in that column, ensuring
# columns are uniformly aligned and wide tables scroll smoothly horizontally.
def _custom_markdown_table_compose(self):
    headers, rows = self._get_headers_and_rows()
    self._headers = headers
    self._rows = rows
    tc = MarkdownTableContent(headers, rows)
    num_cols = len(headers)
    col_widths = [0] * num_cols
    for idx, h in enumerate(headers):
        col_widths[idx] = max(col_widths[idx], cell_len(h.plain))
    for row in rows:
        for idx, cell in enumerate(row):
            if idx < num_cols:
                col_widths[idx] = max(col_widths[idx], cell_len(cell.plain))
    tc.styles.grid_size_columns = num_cols
    tc.styles.grid_columns = [Scalar.from_number(w + 2) for w in col_widths]
    total_w = sum(col_widths) + num_cols * 2 + max(0, num_cols - 1)
    tc.styles.width = total_w
    yield tc

tm.MarkdownTable.compose = _custom_markdown_table_compose


class MarkdownViewerWidget(MarkdownViewer):
    """Integrated Markdown/HTML viewer widget with Mermaid preprocessing and TOC support."""

    DEFAULT_CSS = """
    MarkdownViewerWidget {
        width: 100%;
        height: 100%;
    }
    .-search-match-active {
        background: #d19a66 35%;
        border-left: thick $accent;
        text-style: bold;
    }
    MarkdownBlock .em {
        text-style: italic;
        color: $accent;
    }
    MarkdownBlock .strong {
        text-style: bold;
    }
    MarkdownBlock .s {
        text-style: strike;
    }
    MarkdownBlockQuote {
        text-style: italic;
        color: $text-muted;
        border-left: thick $accent 60%;
        background: $boost;
        padding: 0 1;
        margin: 1 0;
    }
    MarkdownTable {
        width: 1fr;
        height: auto;
        overflow-x: auto;
        overflow-y: hidden;
    }
    """

    def __init__(
        self,
        raw_markdown: str = "",
        show_toc: bool = False,
        filename: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        self.raw_markdown = raw_markdown
        self.filename = filename
        processed_md = self._preprocess(raw_markdown, filename) if raw_markdown else ""
        super().__init__(
            markdown=processed_md,
            show_table_of_contents=show_toc,
            name=name,
            id=id,
            classes=classes,
        )

    def _preprocess(self, text: str, filename: str | None = None) -> str:
        """Auto convert HTML to Markdown if needed, format non-md/html plain text files, then preprocess Mermaid diagrams."""
        content = text
        if is_html_content(content, filename):
            content = html_to_markdown(content)
        elif filename and not is_markdown_file(filename):
            # Treat plain text files (e.g. .txt, .py, .sh, .json, .log, etc.) as verbatim plain text
            content = f"```text\n{content}\n```"
        return preprocess_mermaid(content)

    def update_content(self, markdown_text: str, filename: str | None = None) -> None:
        """Process HTML/Mermaid blocks and update the document."""
        self.raw_markdown = markdown_text
        if filename is not None:
            self.filename = filename
        processed_md = self._preprocess(markdown_text, self.filename)
        self.document.update(processed_md)

    def toggle_toc(self) -> None:
        """Toggle Table of Contents sidebar visibility."""
        self.show_table_of_contents = not self.show_table_of_contents

    def scroll_relative_custom(self, dy: int) -> None:
        """Scroll document up or down."""
        self.scroll_relative(y=dy)

    def scroll_horizontal(self, dx: int) -> None:
        """Scroll wide elements (such as tables and code fences) horizontally."""
        # 1. First scroll viewer itself if it supports horizontal scrolling
        if self.allow_horizontal_scroll and self.max_scroll_x > 0:
            self.scroll_relative(x=dx)
        
        # 2. Scroll any wide code block / markdown table in document
        for child in self.document.children:
            if isinstance(child, (MarkdownFence, MarkdownTable)) and child.max_scroll_x > 0:
                target_x = max(0, min(child.max_scroll_x, child.scroll_x + dx))
                child.scroll_to(x=target_x, immediate=True, animate=False)

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

    def search_text(self, query: str) -> list[object]:
        """Search all blocks/elements containing query string (case-insensitive, deep traversal)."""
        q = query.strip().lower()
        if not q:
            return []

        def get_all_node_text(node: object) -> str:
            pieces = []
            if hasattr(node, "_content") and node._content is not None:
                pieces.append(str(node._content))
            if hasattr(node, "_inline_token") and node._inline_token and node._inline_token.content:
                pieces.append(str(node._inline_token.content))
            if hasattr(node, "text") and node.text:
                pieces.append(str(node.text))
            if hasattr(node, "renderable") and node.renderable:
                pieces.append(str(node.renderable))
            for child in getattr(node, "children", []):
                pieces.append(get_all_node_text(child))
            return " ".join(pieces)

        matches = []
        for block in self.document.children:
            # Check if block has children with granular targets (like list items in MarkdownBulletList / MarkdownOrderedList)
            if hasattr(block, "children") and block.children:
                sub_matched = False
                for sub in block.children:
                    sub_text = get_all_node_text(sub)
                    if q in sub_text.lower():
                        matches.append(sub)
                        sub_matched = True
                if not sub_matched:
                    block_text = get_all_node_text(block)
                    if q in block_text.lower():
                        matches.append(block)
            else:
                block_text = get_all_node_text(block)
                if q in block_text.lower():
                    matches.append(block)
        return matches

    def scroll_to_block(self, block: object) -> None:
        """Scroll document to center or top of matching block widget and highlight it."""
        try:
            self.clear_highlights()
            if hasattr(block, "add_class"):
                block.add_class("-search-match-active")
            self.scroll_to_widget(block, top=True)
        except Exception:
            pass

    def clear_highlights(self) -> None:
        """Remove highlight class from all elements in the document."""
        def clear_node(node: object) -> None:
            if hasattr(node, "remove_class"):
                node.remove_class("-search-match-active")
            for child in getattr(node, "children", []):
                clear_node(child)

        for block in self.document.children:
            clear_node(block)
