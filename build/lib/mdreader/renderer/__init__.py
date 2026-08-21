"""Renderer module."""
from __future__ import annotations
from mdreader.renderer.mermaid import preprocess_mermaid
from mdreader.renderer.html import html_to_markdown, is_html_content

__all__ = ["preprocess_mermaid", "html_to_markdown", "is_html_content"]
