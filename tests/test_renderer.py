"""Unit tests for mermaid preprocessor."""
from mdreader.renderer.mermaid import preprocess_mermaid, render_mermaid_block


def test_render_mermaid_block_valid():
    code = """graph LR
    A --> B
    """
    res = render_mermaid_block(code)
    assert res.startswith("```text\n")
    assert res.endswith("\n```")
    assert "A" in res
    assert "B" in res


def test_render_mermaid_block_invalid_graceful():
    code = "this is not valid mermaid @#$%"
    res = render_mermaid_block(code)
    # Shouldn't crash, should wrap warning and original code
    assert "```text" in res
    assert "Mermaid Render Warning" in res


def test_preprocess_mermaid_mixed():
    md = """# Title
Some text.

```mermaid
graph TD
    Start --> Stop
```

More text.

```python
print("hello")
```
"""
    processed = preprocess_mermaid(md)
    # The mermaid block should be replaced
    assert "```mermaid" not in processed
    assert "Start" in processed
    assert "Stop" in processed
    # Python code block should remain untouched
    assert "```python\nprint(\"hello\")\n```" in processed


def test_html_to_markdown_basic():
    from mdreader.renderer.html import html_to_markdown, is_html_content

    html = """<!DOCTYPE html>
    <html>
    <head><title>Test</title><style>body { color: red; }</style></head>
    <body>
        <h1>標題一</h1>
        <p>這是一段 <strong>粗體</strong> 與 <em>斜體</em> 測試。</p>
        <a href="https://github.com">GitHub 連結</a>
        <ul>
            <li>項目 A</li>
            <li>項目 B</li>
        </ul>
        <pre><code>code block content</code></pre>
        <blockquote>引言內容</blockquote>
        <table>
            <tr><th>欄位 1</th><th>欄位 2</th></tr>
            <tr><td>資料 1</td><td>資料 2</td></tr>
        </table>
    </body>
    </html>
    """
    assert is_html_content(html, "test.html") is True
    assert is_html_content("# Markdown", "test.md") is False

    md = html_to_markdown(html)
    assert "# 標題一" in md
    assert "**粗體**" in md
    assert "*斜體*" in md
    assert "[GitHub 連結](https://github.com)" in md
    assert "* 項目 A" in md
    assert "```\ncode block content\n```" in md
    assert "> 引言內容" in md
    assert "| 欄位 1 | 欄位 2 |" in md
    assert "| 資料 1 | 資料 2 |" in md
    # Should exclude head/style
    assert "color: red" not in md
