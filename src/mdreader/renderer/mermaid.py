"""Mermaid diagram preprocessor module."""
import re
import logging
import termaid

logger = logging.getLogger(__name__)

# Monkey-patch termaid stadium (pill/rounded) node rendering to fix border alignment issue
try:
    import termaid.renderer.shapes as _shapes

    def _aligned_draw_stadium(canvas, x: int, y: int, width: int, height: int, label: str, cs, style: str = "") -> None:
        """Draw a properly aligned stadium shape using clean rounded box corners."""
        # Top border
        canvas.put(y, x, cs.round_top_left, style=style)
        for c in range(x + 1, x + width - 1):
            canvas.put(y, c, cs.horizontal, style=style)
        canvas.put(y, x + width - 1, cs.round_top_right, style=style)

        # Bottom border
        canvas.put(y + height - 1, x, cs.round_bottom_left, style=style)
        for c in range(x + 1, x + width - 1):
            canvas.put(y + height - 1, c, cs.horizontal, style=style)
        canvas.put(y + height - 1, x + width - 1, cs.round_bottom_right, style=style)

        # Side borders
        for r in range(y + 1, y + height - 1):
            canvas.put(r, x, cs.vertical, style=style)
            canvas.put(r, x + width - 1, cs.vertical, style=style)

        _shapes._draw_label(canvas, x, y, width, height, label, style=style)

    _shapes.draw_stadium = _aligned_draw_stadium
    _shapes.SHAPE_RENDERERS[_shapes.NodeShape.STADIUM] = _aligned_draw_stadium
except Exception as _patch_err:
    logger.debug("Could not patch termaid stadium renderer: %s", _patch_err)

# Regular expression matching ```mermaid ... ``` code blocks
MERMAID_BLOCK_PATTERN = re.compile(r"```mermaid[ \t]*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def render_mermaid_block(mermaid_code: str) -> str:
    """Render a single mermaid diagram string to ASCII/Unicode art.
    
    If rendering fails, returns a fallback representation with error details.
    """
    clean_code = mermaid_code.strip()
    if not clean_code:
        return "```text\n(empty mermaid diagram)\n```"

    try:
        rendered_art = termaid.render(clean_code)
        if rendered_art and rendered_art.strip():
            return f"```text\n{rendered_art.strip()}\n```"
        # If termaid returned empty output on non-empty input
        return (
            f"```text\n"
            f"⚠️ [Mermaid Render Warning: Unable to parse diagram syntax]\n"
            f"{clean_code}\n"
            f"```"
        )
    except Exception as exc:
        logger.warning("Failed to render mermaid diagram: %s", exc)
        return (
            f"```text\n"
            f"⚠️ [Mermaid Render Warning: {exc}]\n"
            f"{clean_code}\n"
            f"```"
        )


def preprocess_mermaid(markdown_text: str) -> str:
    """Scan markdown content, convert all mermaid blocks into ASCII code blocks."""
    def _replace_match(match: re.Match) -> str:
        mermaid_code = match.group(1)
        return render_mermaid_block(mermaid_code)

    return MERMAID_BLOCK_PATTERN.sub(_replace_match, markdown_text)
