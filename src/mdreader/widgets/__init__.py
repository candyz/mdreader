"""Widgets module."""
from __future__ import annotations
from mdreader.widgets.markdown_view import MarkdownViewerWidget
from mdreader.widgets.virtual_viewer import VirtualTextViewer, should_use_virtual_viewer
from mdreader.widgets.file_picker import FilePickerScreen
from mdreader.widgets.outline_modal import OutlineModalScreen
from mdreader.widgets.commander import CommanderScreen

__all__ = [
    "MarkdownViewerWidget",
    "VirtualTextViewer",
    "should_use_virtual_viewer",
    "FilePickerScreen",
    "OutlineModalScreen",
    "CommanderScreen",
]
