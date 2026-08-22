"""HTML to Markdown preprocessor module using Python standard library."""
from __future__ import annotations
import re
import io
from html.parser import HTMLParser
from html import unescape


class HTMLToMarkdownParser(HTMLParser):
    """Clean and lightweight HTML to Markdown parser."""

    def __init__(self):
        super().__init__()
        self.output = io.StringIO()
        self.tag_stack: list[str] = []
        self.in_pre = False
        self.list_stack: list[dict] = []  # track 'ul' or 'ol' with counter
        self.table_in_header = False
        self.table_row: list[str] = []
        self.table_rows: list[list[str]] = []
        self.in_table = False
        self.in_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = {k.lower(): v for k, v in attrs if v is not None}
        t = tag.lower()
        self.tag_stack.append(t)

        if t in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(t[1])
            self.output.write("\n\n" + "#" * level + " ")
        elif t == "p":
            self.output.write("\n\n")
        elif t == "br":
            self.output.write("\n")
        elif t == "hr":
            self.output.write("\n\n---\n\n")
        elif t in ("strong", "b"):
            self.output.write("**")
        elif t in ("em", "i"):
            self.output.write("*")
        elif t in ("s", "del", "strike"):
            self.output.write("~~")
        elif t == "code":
            if not self.in_pre:
                self.output.write("`")
        elif t == "pre":
            self.in_pre = True
            lang = ""
            cls = attr_dict.get("class", "")
            match = re.search(r"(?:language-|lang-)([a-zA-Z0-9_-]+)", cls)
            if match:
                lang = match.group(1)
            self.output.write(f"\n\n```{lang}\n")
        elif t == "blockquote":
            self.output.write("\n\n> ")
        elif t == "ul":
            self.list_stack.append({"type": "ul", "count": 0})
            self.output.write("\n")
        elif t == "ol":
            self.list_stack.append({"type": "ol", "count": 0})
            self.output.write("\n")
        elif t == "li":
            indent = "  " * max(0, len(self.list_stack) - 1)
            if self.list_stack and self.list_stack[-1]["type"] == "ol":
                self.list_stack[-1]["count"] += 1
                cnt = self.list_stack[-1]["count"]
                self.output.write(f"\n{indent}{cnt}. ")
            else:
                self.output.write(f"\n{indent}* ")
        elif t == "a":
            href = attr_dict.get("href", "")
            self.output.write("[")
            self._current_href = href
        elif t == "img":
            src = attr_dict.get("src", "")
            alt = attr_dict.get("alt", "image")
            self.output.write(f"![{alt}]({src})")
        elif t == "table":
            self.in_table = True
            self.table_rows = []
        elif t == "thead":
            self.table_in_header = True
        elif t == "tr":
            self.table_row = []
        elif t in ("th", "td"):
            self.in_cell = True
            self._current_cell = io.StringIO()

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if self.tag_stack and self.tag_stack[-1] == t:
            self.tag_stack.pop()

        if t in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.output.write("\n\n")
        elif t == "p":
            self.output.write("\n\n")
        elif t in ("strong", "b"):
            self.output.write("**")
        elif t in ("em", "i"):
            self.output.write("*")
        elif t in ("s", "del", "strike"):
            self.output.write("~~")
        elif t == "code":
            if not self.in_pre:
                self.output.write("`")
        elif t == "pre":
            self.in_pre = False
            self.output.write("\n```\n\n")
        elif t == "blockquote":
            self.output.write("\n\n")
        elif t in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            self.output.write("\n")
        elif t == "a":
            href = getattr(self, "_current_href", "")
            self.output.write(f"]({href})")
        elif t in ("th", "td"):
            self.in_cell = False
            cell_text = getattr(self, "_current_cell", io.StringIO()).getvalue().strip().replace("\n", " ")
            self.table_row.append(cell_text)
        elif t == "tr":
            if self.table_row:
                self.table_rows.append(self.table_row)
        elif t == "thead":
            self.table_in_header = False
        elif t == "table":
            self.in_table = False
            if self.table_rows:
                self._format_table()

    def _format_table(self) -> None:
        """Format captured table rows into GFM markdown table."""
        if not self.table_rows:
            return
        max_cols = max(len(r) for r in self.table_rows)
        if max_cols == 0:
            return
        
        self.output.write("\n\n")
        header = self.table_rows[0]
        padded_header = header + [""] * (max_cols - len(header))
        self.output.write("| " + " | ".join(padded_header) + " |\n")
        self.output.write("| " + " | ".join([":---"] * max_cols) + " |\n")

        for row in self.table_rows[1:]:
            padded_row = row + [""] * (max_cols - len(row))
            self.output.write("| " + " | ".join(padded_row) + " |\n")
        self.output.write("\n\n")

    def handle_data(self, data: str) -> None:
        if self.tag_stack and self.tag_stack[-1] in ("script", "style", "head", "title", "meta"):
            return

        text = unescape(data)
        if self.in_table:
            if self.in_cell and hasattr(self, "_current_cell"):
                self._current_cell.write(text)
            # ignore whitespace between table tags
            return
        
        if self.in_pre:
            self.output.write(text)
        else:
            # collapse spaces inside text if not pre
            cleaned = re.sub(r"[ \t\r\n]+", " ", text) if "\n" in text else text
            self.output.write(cleaned)


def html_to_markdown(html_content: str) -> str:
    """Convert HTML string to clean Markdown formatted text."""
    if not html_content or not html_content.strip():
        return ""
    parser = HTMLToMarkdownParser()
    try:
        parser.feed(html_content)
        parser.close()
        res = parser.output.getvalue()
        # Clean up excessive newlines
        res = re.sub(r"\n{3,}", "\n\n", res).strip()
        return res
    except Exception:
        return html_content


def is_markdown_file(filename: str | None = None) -> bool:
    """Check if filename has a markdown extension."""
    if not filename:
        return False
    fn = filename.lower()
    return fn.endswith((".md", ".markdown", ".mdown", ".mkd", ".mkdn", ".mdwn", ".mdtxt", ".mdtext"))


def detect_code_language(filename: str | None = None) -> str:
    """Detect appropriate programming language alias for syntax highlighting like Vim."""
    if not filename:
        return "text"
    
    # Common extension mappings for fast & accurate lexer selection
    ext_map = {
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".hpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".js": "javascript",
        ".jsx": "jsx",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "zsh",
        ".py": "python",
        ".pyw": "python",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".kt": "kotlin",
        ".swift": "swift",
        ".php": "php",
        ".sql": "sql",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".xml": "xml",
        ".lua": "lua",
        ".vim": "vim",
        ".ini": "ini",
        ".conf": "ini",
    }
    
    import os
    fname = os.path.basename(filename).lower()
    root, ext = os.path.splitext(fname)
    if ext in ext_map:
        return ext_map[ext]
    
    if fname in ("makefile", "gnumakefile"):
        return "makefile"
    if fname in ("dockerfile", "containerfile"):
        return "dockerfile"
    if fname.startswith((".bash", ".zsh", ".profile")):
        return "bash"
    
    try:
        from pygments.lexers import get_lexer_for_filename, ClassNotFound
        lexer = get_lexer_for_filename(filename)
        if lexer.aliases:
            return lexer.aliases[0]
    except Exception:
        pass
    
    return "text"


def is_html_content(text: str, filename: str | None = None) -> bool:
    """Check if content or filename indicates HTML format."""
    if filename:
        fn = filename.lower()
        if fn.endswith((".html", ".htm", ".xhtml")):
            return True
        # If filename is explicitly provided and not an html extension, do not treat as html
        return False
    
    clean = text.strip()[:500].lower()
    if clean.startswith(("<!doctype html", "<html", "<head", "<body")):
        return True
    if re.search(r"<(?:p|div|h[1-6]|table|ul|ol|body|html)(?:\s+[^>]*)?>", clean):
        return True
    return False
