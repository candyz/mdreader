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
