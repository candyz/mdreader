"""Modal dialog for exporting documents to HTML, TXT, or MD formats."""
from __future__ import annotations
from pathlib import Path
from typing import Optional
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Button, RadioSet, RadioButton
from textual.binding import Binding
from mdreader.utils.export import export_document_to_file


class ExportModal(ModalScreen[Optional[Path]]):
    """Modal dialog for choosing export format and destination file path."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
    ]

    CSS = """
    ExportModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.75);
    }
    #export-dialog {
        width: 68;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    #export-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        text-align: center;
    }
    #format-set {
        margin-bottom: 1;
        border: none;
    }
    #path-input {
        width: 100%;
        margin-bottom: 1;
    }
    #export-buttons {
        width: 100%;
        height: 3;
        align: right middle;
    }
    #export-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(
        self,
        content: str,
        current_filepath: Path | None = None,
    ) -> None:
        super().__init__()
        self.content = content
        self.current_filepath = current_filepath
        base_name = current_filepath.stem if current_filepath else "exported_doc"
        self.default_dir = current_filepath.parent if current_filepath else Path.cwd()
        self.default_html_path = self.default_dir / f"{base_name}.html"
        self.selected_format = "html"

    def compose(self) -> ComposeResult:
        with Vertical(id="export-dialog"):
            yield Label("📤 Export Document", id="export-title")
            with RadioSet(id="format-set"):
                yield RadioButton("Standalone HTML Document (.html)", value=True, id="radio-html")
                yield RadioButton("Plain Text File (.txt)", id="radio-txt")
                yield RadioButton("Markdown Source File (.md)", id="radio-md")
            yield Label("Export File Destination Path:")
            yield Input(value=str(self.default_html_path), id="path-input")
            with Horizontal(id="export-buttons"):
                yield Button("Cancel (Esc)", variant="default", id="cancel-btn")
                yield Button("Export (Enter)", variant="primary", id="export-btn")

    def on_mount(self) -> None:
        self.query_one("#path-input", Input).focus()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        path_input = self.query_one("#path-input", Input)
        base_name = self.current_filepath.stem if self.current_filepath else "exported_doc"
        if event.pressed.id == "radio-html":
            self.selected_format = "html"
            path_input.value = str(self.default_dir / f"{base_name}.html")
        elif event.pressed.id == "radio-txt":
            self.selected_format = "txt"
            path_input.value = str(self.default_dir / f"{base_name}.txt")
        elif event.pressed.id == "radio-md":
            self.selected_format = "md"
            path_input.value = str(self.default_dir / f"{base_name}_copy.md")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "export-btn":
            self._do_export()
        elif event.button.id == "cancel-btn":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._do_export()

    def _do_export(self) -> None:
        path_input = self.query_one("#path-input", Input)
        dest_str = path_input.value.strip()
        if not dest_str:
            return

        try:
            title = self.current_filepath.stem if self.current_filepath else "Document"
            out_file = export_document_to_file(
                content=self.content,
                output_path=dest_str,
                export_format=self.selected_format,
                title=title,
            )
            self.dismiss(out_file)
        except Exception as e:
            self.notify(f"Export failed: {e}", title="Error", severity="error")

    def action_cancel(self) -> None:
        self.dismiss(None)
