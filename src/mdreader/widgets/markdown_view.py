"""Markdown viewer widget module with Mermaid preprocessing & TOC support."""
from __future__ import annotations
import textual.widgets._markdown as tm
from textual.widgets import MarkdownViewer
from textual.widgets._markdown import MarkdownTable, MarkdownTableContent, MarkdownFence
from textual.css.scalar import Scalar
from rich.cells import cell_len
from mdreader.renderer.mermaid import preprocess_mermaid
from mdreader.renderer.html import html_to_markdown, is_html_content, is_markdown_file, detect_code_language


from textual.content import Content, Span
from textual.style import Style
from markdown_it.token import Token


# Monkey-patch Textual's MarkdownTable.compose so table columns are proportioned,
# compact columns get fixed neat widths, and wide descriptive text columns (e.g. 說明)
# get 1fr to wrap text across multiple lines and fit within the viewport width (matching leaf/GFM).
def _custom_markdown_table_compose(self):
    headers, rows = self._get_headers_and_rows()
    self._headers = headers
    self._rows = rows
    tc = MarkdownTableContent(headers, rows)
    num_cols = len(headers)
    if num_cols == 0:
        yield tc
        return

    col_widths = [0] * num_cols
    for idx, h in enumerate(headers):
        col_widths[idx] = max(col_widths[idx], cell_len(h.plain))
    for row in rows:
        for idx, cell in enumerate(row):
            if idx < num_cols:
                col_widths[idx] = max(col_widths[idx], cell_len(cell.plain))

    max_w = max(col_widths)
    if num_cols <= 8 and max_w > 20:
        grid_cols = []
        for w in col_widths:
            if w == max_w:
                grid_cols.append(Scalar.parse("1fr"))
            else:
                grid_cols.append(Scalar.from_number(w + 2))
        tc.styles.grid_size_columns = num_cols
        tc.styles.grid_columns = grid_cols
        tc.styles.width = Scalar.parse("100%")
    else:
        tc.styles.grid_size_columns = num_cols
        tc.styles.grid_columns = [Scalar.from_number(w + 2) for w in col_widths]
        total_w = sum(col_widths) + num_cols * 2 + max(0, num_cols - 1)
        tc.styles.width = total_w
    yield tc

tm.MarkdownTable.compose = _custom_markdown_table_compose


# High-performance streamlined table content compose (avoiding heavy per-cell tooltips and redundant selector evaluations)
def _fast_markdown_table_content_compose(self):
    for header in self.headers:
        yield tm.MarkdownTableCellContents(header, classes="header")
    for row_index, row in enumerate(self.rows, 1):
        for cell in row:
            yield tm.MarkdownTableCellContents(cell, classes="cell")
        self.last_row = row_index

tm.MarkdownTableContent.compose = _fast_markdown_table_content_compose


# Streamlined list compose (reduces redundant container wrapping from 5 widgets down to 3 per list item)
def _fast_bullet_list_compose(self):
    for block in self._blocks:
        if isinstance(block, tm.MarkdownListItem):
            bullet = tm.MarkdownBullet()
            bullet.symbol = block.bullet
            if len(block._blocks) == 1:
                yield tm.Horizontal(bullet, block._blocks[0])
            else:
                yield tm.Horizontal(bullet, tm.Vertical(*block._blocks))
    self._blocks.clear()

tm.MarkdownBulletList.compose = _fast_bullet_list_compose


# Lazy TOC rebuild: defer constructing 100+ TreeNode objects until TOC sidebar is actually opened
_orig_rebuild_toc = tm.MarkdownTableOfContents.rebuild_table_of_contents


def _lazy_rebuild_toc(self, table_of_contents):
    self._pending_toc = table_of_contents
    if self.styles.display != "none":
        _orig_rebuild_toc(self, table_of_contents)

tm.MarkdownTableOfContents.rebuild_table_of_contents = _lazy_rebuild_toc

from pygments.token import Token as PygmentsToken


class VimDarkHighlightTheme:
    """Classic Vim Dark Syntax Highlight Theme with bright blue comments."""
    STYLES: dict[PygmentsToken, str] = {
        PygmentsToken.Comment: "#5f87ff",                  # Classic Vim Blue Comments!
        PygmentsToken.Comment.Single: "#5f87ff",
        PygmentsToken.Comment.Multiline: "#5f87ff",
        PygmentsToken.Keyword: "#ffff00 bold",             # Classic Vim Yellow Keywords!
        PygmentsToken.Keyword.Constant: "#ffff00 bold",
        PygmentsToken.Keyword.Namespace: "#ffff00 bold",
        PygmentsToken.Keyword.Type: "#00ffff bold",        # Vim Cyan Type
        PygmentsToken.Literal.Number: "#ff55ff",           # Magenta
        PygmentsToken.Literal.String: "#55ff55",           # Green
        PygmentsToken.Literal.String.Doc: "#5f87ff italic",
        PygmentsToken.Literal.String.Double: "#55ff55",
        PygmentsToken.Literal.String.Single: "#55ff55",
        PygmentsToken.Name: "#ffffff",
        PygmentsToken.Name.Attribute: "#5fd7ff",
        PygmentsToken.Name.Builtin: "#00ffff",             # Cyan
        PygmentsToken.Name.Class: "#00ffff bold",
        PygmentsToken.Name.Constant: "#ff5555",
        PygmentsToken.Name.Function: "#00ffff bold",
        PygmentsToken.Name.Variable: "#00ffff",            # Cyan ($VAR)
        PygmentsToken.Number: "#ff55ff",
        PygmentsToken.Operator: "#ffff00",
        PygmentsToken.Operator.Word: "#ffff00 bold",
        PygmentsToken.String: "#55ff55",
        PygmentsToken.Punctuation: "#ffffff",
        PygmentsToken.Whitespace: "",
    }


_orig_markdown_fence_highlight = MarkdownFence.highlight


def _custom_markdown_fence_highlight(cls, code: str, language: str, ansi: bool = False, dark: bool = False) -> Content:
    try:
        from textual._context import active_app
        app = active_app.get()
        if app and (getattr(app, "theme", None) == "vim-dark" or getattr(getattr(app, "current_theme", None), "name", None) == "vim-dark"):
            from textual.widgets._markdown import highlight
            return highlight(code, language=language or None, theme=VimDarkHighlightTheme)
    except Exception:
        pass
    return _orig_markdown_fence_highlight(code, language, ansi=ansi, dark=dark)


MarkdownFence.highlight = classmethod(_custom_markdown_fence_highlight)


# Monkey-patch Textual's MarkdownBlock._token_to_content to preserve soft linebreaks
# (displaying separate lines rather than collapsing into a single merged paragraph, matching leaf/GFM).
def _custom_token_to_content(self, token: Token) -> Content:
    if token.children is None:
        return Content("")

    tokens: list[str] = []
    spans: list[Span] = []
    style_stack: list[tuple[Style | str, int]] = []
    position: int = 0

    def add_content(text: str) -> None:
        nonlocal position
        tokens.append(text)
        position += len(text)

    def add_style(style: Style | str) -> None:
        style_stack.append((style, position))

    def close_tag() -> None:
        if style_stack:
            style, start = style_stack.pop()
            spans.append(Span(start, position, style))

    for child in token.children:
        child_type = child.type
        if child_type == "text":
            add_content(child.content)
        elif child_type in ("hardbreak", "softbreak"):
            add_content("\n")
        elif child_type == "code_inline":
            add_style(".code_inline")
            add_content(child.content)
            close_tag()
        elif child_type == "em_open":
            add_style(".em")
        elif child_type == "strong_open":
            add_style(".strong")
        elif child_type == "s_open":
            add_style(".s")
        elif child_type == "link_open":
            href = child.attrs.get("href", "")
            action = f"link({href!r})"
            add_style(Style.from_meta({"@click": action}))
        elif child_type == "image":
            href = child.attrs.get("src", "")
            alt = child.attrs.get("alt", "")
            action = f"link({href!r})"
            add_style(Style.from_meta({"@click": action}))
            add_content("🖼  ")
            if alt:
                add_content(f"({alt})")
            if child.children is not None:
                for grandchild in child.children:
                    add_content(grandchild.content)
            close_tag()
        elif child_type.endswith("_close"):
            close_tag()

    return Content("".join(tokens), spans=spans)

tm.MarkdownBlock._token_to_content = _custom_token_to_content


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
    MarkdownBlockQuote {
        text-style: italic;
        color: $text-muted;
        border-left: thick $accent 60%;
        background: $boost;
        padding: 0 1;
        margin: 1 0;
    }
    MarkdownViewerWidget MarkdownTable {
        overflow-x: auto;
        overflow-y: hidden;
    }
    MarkdownViewerWidget MarkdownFence {
        overflow-x: auto;
        overflow-y: hidden;
    }
    MarkdownViewerWidget.-no-wrap {
        overflow-x: auto;
    }
    MarkdownViewerWidget.-no-wrap > Markdown {
        width: auto;
        min-width: 100%;
    }
    MarkdownViewerWidget.-no-wrap MarkdownBlock {
        text-wrap: nowrap;
        width: auto;
    }
    MarkdownViewerWidget.-no-wrap MarkdownTable {
        overflow-x: auto;
        width: auto;
    }
    """

    def __init__(
        self,
        raw_markdown: str = "",
        show_toc: bool = False,
        filename: str | None = None,
        syntax: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        self.raw_markdown = raw_markdown
        self.filename = filename
        self.syntax = syntax
        self.soft_wrap: bool = True
        processed_md = self._preprocess(raw_markdown, filename) if raw_markdown else ""
        super().__init__(
            markdown=processed_md,
            show_table_of_contents=show_toc,
            name=name,
            id=id,
            classes=classes,
        )

    def watch_show_table_of_contents(self, show_table_of_contents: bool) -> None:
        """On-demand rebuild of TOC tree when sidebar is opened."""
        super().watch_show_table_of_contents(show_table_of_contents)
        if show_table_of_contents:
            try:
                toc = self.query_one(tm.MarkdownTableOfContents)
                if getattr(toc, "_pending_toc", None):
                    _orig_rebuild_toc(toc, toc._pending_toc)
            except Exception:
                pass

    def set_soft_wrap(self, wrap: bool) -> None:
        """Toggle soft wrapping in Markdown viewer."""
        self.soft_wrap = wrap
        if wrap:
            self.remove_class("-no-wrap")
            self.scroll_x = 0
        else:
            self.add_class("-no-wrap")
        try:
            if self.is_mounted and hasattr(self, "document"):
                self.document.refresh()
        except Exception:
            pass

    def _preprocess(self, text: str, filename: str | None = None) -> str:
        """Auto convert HTML to Markdown if needed, format code/plain text files with syntax highlighting, then preprocess Mermaid diagrams."""
        content = text
        if is_html_content(content, filename):
            content = html_to_markdown(content)
        elif filename and not is_markdown_file(filename):
            # Treat code & plain text files (e.g. .c, .h, .js, .css, .sh, .py, etc.) as syntax-highlighted code blocks
            lang = self.syntax or detect_code_language(filename)
            if lang and lang.lower() not in ("none", "plain", "text"):
                content = f"```{lang}\n{content}\n```"
            else:
                content = f"```\n{content}\n```"
        elif not filename and self.syntax and self.syntax.lower() not in ("none", "plain", "text"):
            content = f"```{self.syntax}\n{content}\n```"
        return preprocess_mermaid(content)

    def update_content(self, markdown_text: str, filename: str | None = None, syntax: str | None = None) -> None:
        """Process HTML/Mermaid blocks and update the document."""
        self.raw_markdown = markdown_text
        if filename is not None:
            self.filename = filename
        if syntax is not None:
            self.syntax = syntax
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
            self.scroll_relative(x=dx, animate=False)
        
        # 2. Scroll any wide code block / markdown table in document
        try:
            for child in self.document.children:
                if isinstance(child, (MarkdownFence, MarkdownTable)) and child.max_scroll_x > 0:
                    child.scroll_relative(x=dx, animate=False)
        except Exception:
            pass

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
