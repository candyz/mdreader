"""Mermaid diagram preprocessor module."""
import re
import logging
import termaid

logger = logging.getLogger(__name__)

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
