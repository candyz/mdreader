"""Terminal Graphics Protocol Helper (iTerm2, Kitty, Sixel detection and image generation)."""
from __future__ import annotations
import os
import sys
import base64
import shutil
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def is_iterm2_supported() -> bool:
    """Check if the current terminal supports iTerm2 inline images protocol."""
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    lc_terminal = os.environ.get("LC_TERMINAL", "").lower()
    return "iterm" in term_program or "wezterm" in term_program or "iterm" in lc_terminal


def is_kitty_supported() -> bool:
    """Check if the current terminal supports Kitty graphics protocol."""
    term = os.environ.get("TERM", "").lower()
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    return "kitty" in term or "kitty" in term_program or "ghostty" in term_program


def render_mermaid_to_png(mermaid_code: str) -> Optional[Path]:
    """Attempts to render Mermaid code to a temporary PNG file using mmdc if installed."""
    mmdc_path = shutil.which("mmdc")
    if not mmdc_path:
        return None

    try:
        with tempfile.NamedTemporaryFile(suffix=".mmd", mode="w", encoding="utf-8", delete=False) as mmd_file:
            mmd_file.write(mermaid_code)
            mmd_path = mmd_file.name

        png_path = mmd_path.replace(".mmd", ".png")
        cmd = [mmdc_path, "-i", mmd_path, "-o", png_path, "-b", "transparent"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and os.path.exists(png_path):
            return Path(png_path)
        else:
            logger.warning("mmdc failed: %s", res.stderr)
            return None
    except Exception as exc:
        logger.warning("Error running mmdc: %s", exc)
        return None


def encode_iterm2_image(image_path: Path) -> str:
    """Encode an image file using iTerm2 inline image escape sequence."""
    try:
        data = image_path.read_bytes()
        b64_data = base64.b64encode(data).decode("ascii")
        size = len(data)
        # OSC 1337 ; File=size=...;inline=1:<base64> ^G
        return f"\033]1337;File=inline=1;size={size}:{b64_data}\a"
    except Exception as e:
        logger.warning("Failed to encode iterm2 image: %s", e)
        return ""
