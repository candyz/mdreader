"""High-performance virtualized line viewer for large files and source code."""
from __future__ import annotations
from pathlib import Path
from textual.scroll_view import ScrollView
from textual.geometry import Size
from textual.strip import Strip
from rich.segment import Segment
from rich.style import Style
import pygments
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
from mdreader.renderer.html import is_markdown_file, is_html_content, detect_code_language

LARGE_FILE_LINE_THRESHOLD = 3000

TOKEN_STYLES = {
    Token.Keyword: Style(color="magenta", bold=True),
    Token.Keyword.Constant: Style(color="magenta", bold=True),
    Token.Keyword.Type: Style(color="bright_cyan"),
    Token.Name.Function: Style(color="bright_blue", bold=True),
    Token.Name.Class: Style(color="bright_cyan", bold=True),
    Token.Name.Builtin: Style(color="cyan"),
    Token.Name.Variable: Style(color="bright_blue"),
    Token.String: Style(color="green"),
    Token.String.Doc: Style(color="green", italic=True),
    Token.Number: Style(color="bright_cyan"),
    Token.Comment: Style(color="bright_black", italic=True),
    Token.Operator: Style(color="bright_yellow"),
    Token.Punctuation: Style(color="grey70"),
}


def get_style_for_token(ttype: Token) -> Style | None:
    while ttype:
        if ttype in TOKEN_STYLES:
            return TOKEN_STYLES[ttype]
        ttype = ttype.parent
    return None


def should_use_virtual_viewer(content: str, filename: str | None) -> bool:
    """Determine whether to use the high-performance VirtualTextViewer instead of MarkdownViewer."""
    if not filename and not content:
        return False
    # Non-markdown code/text files use virtual viewer for instant responsiveness
    if filename and not is_markdown_file(filename) and not is_html_content(content, filename):
        return True
    # Markdown files exceeding threshold use virtual viewer to prevent DOM tree freeze
    line_count = content.count("\n") + 1
    if line_count > LARGE_FILE_LINE_THRESHOLD:
        return True
    return False


from mdreader.utils.mmap_buffer import MmapLineBuffer, MMAP_THRESHOLD_BYTES


class VirtualTextViewer(ScrollView):
    """Virtualized scrollable line viewer rendering only the visible viewport lines (O(1) DOM)."""

    DEFAULT_CSS = """
    VirtualTextViewer {
        width: 100%;
        height: 100%;
        background: $surface;
        color: $text;
    }
    """

    def __init__(
        self,
        raw_text: str | Sequence[str] = "",
        lines: Sequence[str] | None = None,
        filename: str | None = None,
        syntax: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.filename = filename
        self.syntax = syntax
        if lines is not None:
            self.lines = lines
            self.raw_text = ""
        elif isinstance(raw_text, (list, tuple, MmapLineBuffer)):
            self.lines = raw_text
            self.raw_text = ""
        else:
            self.raw_text = raw_text
            self.lines = raw_text.splitlines() if raw_text else []
        self._highlighted_line: int | None = None
        self._search_query: str = ""
        self.show_line_numbers: bool = True
        self.soft_wrap: bool = False
        self.document = self  # Duck-type compatibility with MarkdownViewerWidget
        self._lexer = None
        self._setup_lexer()
        self._update_virtual_size()

    def toggle_line_numbers(self) -> bool:
        """Toggle display of line number column."""
        self.show_line_numbers = not self.show_line_numbers
        self._update_virtual_size()
        self.refresh()
        return self.show_line_numbers

    def set_soft_wrap(self, wrap: bool) -> None:
        """Toggle soft wrapping in virtual viewer."""
        self.soft_wrap = wrap
        self.scroll_x = 0
        self._update_virtual_size()
        self.refresh()

    def _setup_lexer(self) -> None:
        """Initialize lightweight Pygments lexer based on filename extension or syntax override."""
        self._lexer = None
        lang = self.syntax or (detect_code_language(self.filename) if self.filename else detect_code_language(None))
        if lang and lang.lower() not in ("text", "none", "plain"):
            try:
                self._lexer = get_lexer_by_name(lang)
            except Exception:
                try:
                    self._lexer = get_lexer_by_name("bash")
                except Exception:
                    self._lexer = None

    def _compute_display_lines(self) -> None:
        """Compute display lines when soft_wrap is True, or use raw lines when False."""
        if not self.soft_wrap:
            self._display_lines = self.lines
            self._line_map = None
            return

        viewport_w = self.size.width if self.size and self.size.width > 0 else 80
        prefix_len = 8 if self.show_line_numbers else 0
        w = max(20, viewport_w - prefix_len - 2)

        wrapped = []
        line_map = []
        for orig_idx, line in enumerate(self.lines):
            line_expanded = line.expandtabs(4) if "\t" in line else line
            if not line_expanded:
                wrapped.append("")
                line_map.append((orig_idx, True))
            elif len(line_expanded) <= w:
                wrapped.append(line_expanded)
                line_map.append((orig_idx, True))
            else:
                chunks = [line_expanded[i:i+w] for i in range(0, len(line_expanded), w)]
                for chunk_idx, chunk in enumerate(chunks):
                    wrapped.append(chunk)
                    line_map.append((orig_idx, chunk_idx == 0))
        self._display_lines = wrapped
        self._line_map = line_map

    def _update_virtual_size(self) -> None:
        self._compute_display_lines()
        display_lines = getattr(self, "_display_lines", self.lines)
        if self.soft_wrap:
            width = max(40, self.size.width if self.size and self.size.width > 0 else 80)
            self.virtual_size = Size(width, len(display_lines))
            return
        sample = self.lines[:2000] if len(self.lines) > 2000 else self.lines
        max_len = max((len(l.expandtabs(4)) for l in sample), default=80)
        prefix_len = 8 if self.show_line_numbers else 0
        self.virtual_size = Size(max_len + prefix_len + 4, len(self.lines))

    def on_resize(self, event) -> None:
        if self.soft_wrap:
            self._update_virtual_size()
            self.refresh()

    def update_content(self, text: str | Sequence[str], filename: str | None = None, syntax: str | None = None) -> None:
        """Update content and reset virtual geometry."""
        if filename is not None:
            self.filename = filename
        if syntax is not None:
            self.syntax = syntax
        if isinstance(text, (list, tuple, MmapLineBuffer)):
            self.lines = text
            self.raw_text = ""
        else:
            self.raw_text = text
            self.lines = text.splitlines() if text else []
        self._highlighted_line = None
        self._search_query = ""
        self._setup_lexer()
        self._update_virtual_size()
        self.refresh()

    def render_line(self, y: int) -> Strip:
        scroll_y = int(self.scroll_y)
        scroll_x = int(self.scroll_x)
        idx = scroll_y + y
        width = self.size.width if self.size and self.size.width > 0 else 80

        display_lines = getattr(self, "_display_lines", self.lines)
        if not (0 <= idx < len(display_lines)):
            return Strip.blank(width)

        raw_line_str = display_lines[idx]
        line_str = raw_line_str.expandtabs(4) if "\t" in raw_line_str else raw_line_str
        if not self.soft_wrap and scroll_x > 0:
            line_str = line_str[scroll_x:] if scroll_x < len(line_str) else ""

        segments: list[Segment] = []

        # Optional line numbers
        if self.show_line_numbers:
            line_map = getattr(self, "_line_map", None)
            if line_map and idx < len(line_map):
                orig_idx, is_first = line_map[idx]
                line_no = f"{orig_idx + 1:>6} │ " if is_first else "       │ "
            else:
                line_no = f"{idx + 1:>6} │ "
            segments.append(Segment(line_no, Style(color="grey50")))

        # Highlight if explicitly jumped to
        if idx == self._highlighted_line:
            segments.append(Segment(line_str, Style(bgcolor="rgb(209,154,102)", color="black", bold=True)))
            strip = Strip(segments)
            return strip.adjust_cell_length(width, Style()) if width > 0 else strip

        # Highlight search query in real-time
        if self._search_query and self._search_query in line_str.lower():
            q = self._search_query
            lower = line_str.lower()
            start = 0
            while True:
                found = lower.find(q, start)
                if found == -1:
                    if start < len(line_str):
                        segments.append(Segment(line_str[start:]))
                    break
                if found > start:
                    segments.append(Segment(line_str[start:found]))
                segments.append(Segment(line_str[found:found + len(q)], Style(bgcolor="yellow", color="black", bold=True)))
                start = found + len(q)
            strip = Strip(segments)
            return strip.adjust_cell_length(width, Style()) if width > 0 else strip

        # On-demand syntax highlighting via Pygments
        if self._lexer:
            try:
                for ttype, val in pygments.lex(line_str, self._lexer):
                    val = val.rstrip("\r\n")
                    if not val:
                        continue
                    style = get_style_for_token(ttype)
                    segments.append(Segment(val, style))
                strip = Strip(segments)
                return strip.adjust_cell_length(width, Style()) if width > 0 else strip
            except Exception:
                pass

        segments.append(Segment(line_str))
        strip = Strip(segments)
        return strip.adjust_cell_length(width, Style()) if width > 0 else strip

    def scroll_relative_custom(self, dy: int) -> None:
        self.scroll_relative(y=dy)

    def scroll_horizontal(self, dx: int) -> None:
        self.scroll_relative(x=dx)

    def page_down(self) -> None:
        self.scroll_relative(y=max(1, self.size.height - 2))

    def page_up(self) -> None:
        self.scroll_relative(y=-max(1, self.size.height - 2))

    def scroll_home(self) -> None:
        if self.is_mounted:
            self.scroll_to(y=0, animate=False)
        else:
            self.scroll_y = 0.0

    def scroll_end(self) -> None:
        if self.is_mounted:
            self.scroll_to(y=self.max_scroll_y, animate=False)
        else:
            self.scroll_y = float(self.max_scroll_y)

    def get_headings(self) -> list[tuple[int, str, str]]:
        """Extract markdown headings with line index as block_id."""
        headings = []
        for idx, line in enumerate(self.lines):
            l = line.strip()
            if l.startswith("# "):
                headings.append((1, l[2:].strip(), str(idx)))
            elif l.startswith("## "):
                headings.append((2, l[3:].strip(), str(idx)))
            elif l.startswith("### "):
                headings.append((3, l[4:].strip(), str(idx)))
        return headings

    def scroll_to_heading_id(self, block_id: str) -> None:
        """Jump directly to line index of heading."""
        try:
            line_idx = int(block_id)
            self._highlighted_line = line_idx
            if self.is_mounted:
                self.scroll_to(y=line_idx, animate=False)
            else:
                self.scroll_y = float(line_idx)
            self.refresh()
        except ValueError:
            pass

    def search_text(self, query: str) -> list[object]:
        """Fast substring search returning matching line indices."""
        q = query.strip()
        self._search_query = q.lower()
        if not q:
            return []

        # Use lightning-fast memory-mapped binary search if available
        if hasattr(self.lines, "search_text"):
            return self.lines.search_text(q, case_sensitive=False)

        q_lower = q.lower()
        matches: list[object] = []
        for idx, line in enumerate(self.lines):
            if q_lower in line.lower():
                matches.append(idx)
        return matches

    def scroll_to_block(self, block: object) -> None:
        """Scroll to matching line and highlight it."""
        if isinstance(block, int):
            self._highlighted_line = block
            if self.is_mounted:
                self.scroll_to(y=block, animate=False)
            else:
                self.scroll_y = float(block)
            self.refresh()

    def clear_highlights(self) -> None:
        self._highlighted_line = None
        self._search_query = ""
        self.refresh()

    def toggle_toc(self) -> None:
        pass
