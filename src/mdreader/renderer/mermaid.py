"""Mermaid diagram preprocessor module."""
from __future__ import annotations
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
FENCED_BLOCK_PATTERN = re.compile(r"(```[^\n]*\n)(.*?)(```)", re.DOTALL)

_BOX_TOP_RE = re.compile(r"^([ \t]*)([┌╭╔])([─═┬┴┼▼▲▽△]+)([┐╮╗])[ \t]*$")
_BOX_DIV_RE = re.compile(r"^([ \t]*)([├╟╠])([─═┬┴┼▼▲▽△]+)([┤╢╣])[ \t]*$")
_BOX_BOT_RE = re.compile(r"^([ \t]*)([└╰╚])([─═┬┴┼▼▲▽△]+)([┘╯╝])[ \t]*$")
_BOX_ROW_RE = re.compile(r"^([ \t]*)([│║])(.*)([│║])[ \t]*$")


def align_box_drawings(code: str) -> str:
    """Align right borders of Unicode box-drawing diagrams inside a code block.

    Compensates for CJK full-width character miscalculations in hand-drawn or
    LLM-generated ASCII/Unicode boxes (┌──┐ / │..│ / └──┘).
    """
    if not any(ch in code for ch in ("┌", "╭", "╔")):
        return code

    from rich.cells import cell_len

    lines = code.split("\n")
    n = len(lines)
    boxes: list[tuple[int, int, str, int, int]] = []
    i = 0
    while i < n:
        m_top = _BOX_TOP_RE.match(lines[i])
        if not m_top:
            i += 1
            continue
        indent = m_top.group(1)
        j = i + 1
        valid = False
        while j < n:
            m_bot = _BOX_BOT_RE.match(lines[j])
            if m_bot and m_bot.group(1) == indent:
                valid = True
                break
            m_div = _BOX_DIV_RE.match(lines[j])
            m_row = _BOX_ROW_RE.match(lines[j])
            if (m_div and m_div.group(1) == indent) or (m_row and m_row.group(1) == indent):
                j += 1
            else:
                break
        if not valid:
            i += 1
            continue
        m_bot = _BOX_BOT_RE.match(lines[j])
        assert m_bot is not None
        orig_inner = max(cell_len(m_top.group(3)), cell_len(m_bot.group(3)))
        req_inner = orig_inner
        for k in range(i + 1, j):
            mr = _BOX_ROW_RE.match(lines[k])
            if mr:
                stripped_w = cell_len(mr.group(3).rstrip())
                if stripped_w > req_inner:
                    req_inner = stripped_w + (1 if mr.group(3).endswith(" ") else 0)
        boxes.append((i, j, indent, orig_inner, req_inner))
        i = j + 1

    if not boxes:
        return code

    group_target: dict[tuple[str, int], int] = {}
    for _, _, indent, orig_inner, req_inner in boxes:
        key = (indent, orig_inner)
        group_target[key] = max(group_target.get(key, orig_inner), req_inner)

    for i, j, indent, orig_inner, _ in boxes:
        target_inner = group_target[(indent, orig_inner)]
        for idx, rx in ((i, _BOX_TOP_RE), (j, _BOX_BOT_RE)):
            m_border = rx.match(lines[idx])
            if m_border:
                ind, lc, mid, rc = m_border.groups()
                diff = target_inner - cell_len(mid)
                if diff > 0:
                    fill = "═" if "═" in mid else "─"
                    lines[idx] = f"{ind}{lc}{mid}{fill * diff}{rc}"
        for k in range(i + 1, j):
            md = _BOX_DIV_RE.match(lines[k])
            if md:
                ind, lc, mid, rc = md.groups()
                diff = target_inner - cell_len(mid)
                if diff > 0:
                    fill = "═" if "═" in mid else "─"
                    lines[k] = f"{ind}{lc}{mid}{fill * diff}{rc}"
                continue
            mr = _BOX_ROW_RE.match(lines[k])
            if mr:
                ind, lc, body, rc = mr.groups()
                stripped = body.rstrip()
                sw = cell_len(stripped)
                if sw <= target_inner:
                    lines[k] = f"{ind}{lc}{stripped}{' ' * (target_inner - sw)}{rc}"
    return "\n".join(lines)


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
            return f"```text\n{rendered_art.strip('\r\n')}\n```"
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
    """Scan markdown content, convert all mermaid blocks into ASCII code blocks,
    and align Unicode box-drawing borders in fenced code blocks."""
    def _replace_fence(match: re.Match) -> str:
        open_fence, body, close_fence = match.groups()
        if open_fence[3:].strip().lower() == "mermaid":
            return render_mermaid_block(body)
        return f"{open_fence}{align_box_drawings(body)}{close_fence}"

    return FENCED_BLOCK_PATTERN.sub(_replace_fence, markdown_text)
