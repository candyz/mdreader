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


def test_is_markdown_file():
    from mdreader.renderer.html import is_markdown_file

    assert is_markdown_file("test.md") is True
    assert is_markdown_file("doc.markdown") is True
    assert is_markdown_file("notes.mdown") is True
    assert is_markdown_file("test.txt") is False
    assert is_markdown_file("script.py") is False
    assert is_markdown_file("index.html") is False
    assert is_markdown_file(None) is False


def test_detect_code_language():
    from mdreader.renderer.html import detect_code_language

    assert detect_code_language("main.c") == "c"
    assert detect_code_language("header.h") == "c"
    assert detect_code_language("app.js") == "javascript"
    assert detect_code_language("style.css") == "css"
    assert detect_code_language("deploy.sh") == "bash"
    assert detect_code_language("script.py") == "python"
    assert detect_code_language("Makefile") == "makefile"
    assert detect_code_language("Dockerfile") == "dockerfile"
    assert detect_code_language("notes.txt") == "text"


def test_code_and_plain_text_preprocessing():
    from mdreader.widgets.markdown_view import MarkdownViewerWidget

    widget = MarkdownViewerWidget()
    
    # Python file should be highlighted as python
    py_content = "def foo():\n    return 42\n"
    res_py = widget._preprocess(py_content, filename="script.py")
    assert res_py.startswith("```python\n")
    assert "def foo():" in res_py
    assert res_py.endswith("\n```")

    # C file should be highlighted as c
    c_content = '#include <stdio.h>\nint main() { return 0; }'
    res_c = widget._preprocess(c_content, filename="main.c")
    assert res_c.startswith("```c\n")
    assert "#include <stdio.h>" in res_c

    # Header file (.h) should be highlighted as c
    h_content = '#ifndef HEADER_H\n#define HEADER_H\n#endif'
    res_h = widget._preprocess(h_content, filename="header.h")
    assert res_h.startswith("```c\n")

    # JS file should be highlighted as javascript
    js_content = 'console.log("hello");'
    res_js = widget._preprocess(js_content, filename="app.js")
    assert res_js.startswith("```javascript\n")

    # CSS file should be highlighted as css
    css_content = 'body { background: #000; }'
    res_css = widget._preprocess(css_content, filename="style.css")
    assert res_css.startswith("```css\n")

    # Shell script should be highlighted as bash
    sh_content = '#!/bin/bash\necho "test"'
    res_sh = widget._preprocess(sh_content, filename="build.sh")
    assert res_sh.startswith("```bash\n")

    # Markdown file should not be wrapped into code fence
    md_content = "# Header\nHello world"
    res_md = widget._preprocess(md_content, filename="readme.md")
    assert res_md.startswith("# Header")
