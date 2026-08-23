"""Document export utilities for generating standalone HTML, text, and formatted files."""
from __future__ import annotations
from pathlib import Path
from markdown_it import MarkdownIt

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    max-width: 860px;
    margin: 40px auto;
    padding: 0 20px;
    line-height: 1.6;
    color: #24292e;
    background: #ffffff;
}}
@media (prefers-color-scheme: dark) {{
    body {{
        color: #c9d1d9;
        background: #0d1117;
    }}
    a {{ color: #58a6ff; }}
    pre, code {{ background: #161b22 !important; color: #e6edf3; }}
    blockquote {{ border-left-color: #30363d !important; color: #8b949e !important; }}
    th, td {{ border-color: #30363d !important; }}
    tr:nth-child(2n) {{ background: rgba(110, 118, 129, 0.1) !important; }}
}}
pre {{
    background: #f6f8fa;
    padding: 16px;
    border-radius: 6px;
    overflow-x: auto;
}}
code {{
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    font-size: 88%;
    background: rgba(175, 184, 193, 0.2);
    padding: 0.2em 0.4em;
    border-radius: 4px;
}}
pre code {{
    background: transparent;
    padding: 0;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
}}
th, td {{
    border: 1px solid #d0d7de;
    padding: 6px 13px;
}}
tr:nth-child(2n) {{
    background: rgba(175, 184, 193, 0.1);
}}
blockquote {{
    margin: 0;
    padding: 0 1em;
    color: #57606a;
    border-left: 0.25em solid #d0d7de;
}}
h1, h2, h3, h4 {{
    margin-top: 24px;
    margin-bottom: 16px;
    font-weight: 600;
    line-height: 1.25;
}}
h1, h2 {{
    border-bottom: 1px solid #d0d7de;
    padding-bottom: 0.3em;
}}
</style>
</head>
<body>
{body}
</body>
</html>"""


def export_to_html(markdown_text: str, title: str = "Exported Document") -> str:
    """Convert Markdown text to styled standalone HTML document."""
    try:
        md = MarkdownIt("gfm-like", {"breaks": True})
        html_body = md.render(markdown_text)
    except Exception:
        # Fallback to preformatted text if markdown parsing fails
        import html
        html_body = f"<pre>{html.escape(markdown_text)}</pre>"
    return HTML_TEMPLATE.format(title=title, body=html_body)


def export_document_to_file(
    content: str,
    output_path: Path | str,
    export_format: str = "html",
    title: str = "Document",
) -> Path:
    """Export document content to specified output file format."""
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    if export_format == "html":
        rendered = export_to_html(content, title=title)
        out.write_text(rendered, encoding="utf-8")
    elif export_format == "txt":
        out.write_text(content, encoding="utf-8")
    elif export_format == "md":
        out.write_text(content, encoding="utf-8")
    else:
        out.write_text(content, encoding="utf-8")

    return out
