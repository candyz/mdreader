"""Textual Application for Markdown Reader."""
from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, Label
from textual.containers import Container, Vertical
from textual.reactive import reactive
from mdreader.widgets.markdown_view import MarkdownViewerWidget
from mdreader.utils.file_watcher import FileWatcher


class MDReaderApp(App):
    """Interactive TUI Markdown Reader Application."""

    TITLE = "mdreader"
    SUB_TITLE = "Terminal Markdown Viewer"

    THEME_LIST = [
        "textual-dark",
        "textual-light",
        "tokyo-night",
        "monokai",
        "solarized-dark",
        "solarized-light",
        "catppuccin-frappe",
        "catppuccin-latte",
        "dracula",
        "nord",
    ]

    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #reader-box {
        width: 100%;
        height: 100%;
    }

    #search-bar {
        dock: bottom;
        height: auto;
        padding: 0 1;
        background: $panel;
        display: none;
        border-top: solid $primary;
    }

    #search-bar.-visible {
        display: block;
    }

    #search-input {
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("escape", "handle_escape", "Cancel/Back", show=False),
        Binding("t", "toggle_theme", "Theme", show=True),
        Binding("tab", "toggle_toc", "Outline (大綱)", show=True, priority=True),
        Binding("o", "open_file_picker", "Open File", show=True),
        Binding("slash", "open_search", "Search", show=True),
        Binding("j", "page_up", "Page Up", show=False),
        Binding("k", "page_down", "Page Down", show=False),
        Binding("up", "scroll_up", "Up", show=False),
        Binding("down", "scroll_down", "Down", show=False),
        Binding("G", "scroll_end", "Scroll End (Bottom)", show=False),
        Binding("r", "reload_file", "Reload", show=False),
    ]

    search_visible = reactive(False)

    def __init__(
        self,
        content: str = "",
        filepath: Path | str | None = None,
        max_width: int | None = None,
        watch: bool = False,
        theme: str | None = None,
        show_toc: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.content = content
        self.filepath = Path(filepath) if filepath else None
        self.max_width = max_width
        self.watch = watch
        self.show_toc = show_toc
        self._custom_theme = theme
        self._theme_index = 0
        self._watcher: FileWatcher | None = None
        self._last_g_press_time: float = 0.0

        if self.filepath:
            self.SUB_TITLE = str(self.filepath.name)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            with Container(id="reader-box"):
                yield MarkdownViewerWidget(
                    raw_markdown=self.content,
                    show_toc=self.show_toc,
                    id="viewer",
                )
        with Vertical(id="search-bar"):
            yield Input(placeholder="Type to search in document... (Enter to confirm, Esc to dismiss)", id="search-input")
        yield Footer()

    def on_mount(self) -> None:
        if self.max_width:
            reader_box = self.query_one("#reader-box")
            reader_box.styles.max_width = self.max_width

        if self._custom_theme:
            if self._custom_theme in self.available_themes:
                self.theme = self._custom_theme
        
        # Ensure focus is on markdown document for immediate keyboard response
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        viewer.document.focus()

        # Start file watcher if watch mode is enabled
        if self.watch and self.filepath and self.filepath.exists():
            self._watcher = FileWatcher(
                filepath=self.filepath,
                on_modified=self._on_file_changed,
            )
            self._watcher.start()

    def on_unmount(self) -> None:
        if self._watcher:
            self._watcher.stop()
            self._watcher = None

    def _on_file_changed(self) -> None:
        """Invoked in background thread by FileWatcher."""
        self.call_from_thread(self.action_reload_file)

    def action_reload_file(self) -> None:
        """Reload file content from disk and update viewer."""
        if self.filepath and self.filepath.exists():
            try:
                new_content = self.filepath.read_text(encoding="utf-8")
                viewer = self.query_one("#viewer", MarkdownViewerWidget)
                viewer.update_content(new_content)
                self.notify("Document reloaded", title="Auto-Reload", timeout=2)
            except Exception as e:
                self.notify(f"Reload failed: {e}", title="Error", severity="error")

    def action_toggle_toc(self) -> None:
        """Open full outline modal for chapter browsing and jumping."""
        from mdreader.widgets.outline_modal import OutlineModalScreen
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        headings = viewer.get_headings()
        if not headings:
            self.notify("No headings found in document", title="Outline", timeout=1.5)
            return
        self.push_screen(OutlineModalScreen(headings), self._on_outline_selected)

    def _on_outline_selected(self, target_block_id: str | None) -> None:
        """Callback when a heading is selected from Outline modal."""
        if target_block_id:
            viewer = self.query_one("#viewer", MarkdownViewerWidget)
            viewer.scroll_to_heading_id(target_block_id)
            viewer.document.focus()

    def action_toggle_theme(self) -> None:
        """Cycle through available color themes."""
        # Find next valid theme
        valid_themes = [t for t in self.THEME_LIST if t in self.available_themes]
        if not valid_themes:
            return
        self._theme_index = (self._theme_index + 1) % len(valid_themes)
        new_theme = valid_themes[self._theme_index]
        self.theme = new_theme
        self.notify(f"Theme switched to: {new_theme}", timeout=1.5)

    def action_open_search(self) -> None:
        """Open in-document search bar."""
        search_bar = self.query_one("#search-bar")
        search_bar.add_class("-visible")
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        search_input.focus()
        self.search_visible = True

    def action_handle_escape(self) -> None:
        """Escape handles closing search bar or quitting."""
        if self.search_visible:
            search_bar = self.query_one("#search-bar")
            search_bar.remove_class("-visible")
            viewer = self.query_one("#viewer", MarkdownViewerWidget)
            viewer.focus()
            self.search_visible = False
        else:
            self.exit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search submission."""
        query = event.value.strip()
        if query:
            # Dismiss search bar and notify
            self.action_handle_escape()
            self.notify(f"Searching for: '{query}'", timeout=2)
        else:
            self.action_handle_escape()

    def action_open_file_picker(self) -> None:
        """Open fuzzy file picker modal."""
        from mdreader.widgets.file_picker import FilePickerScreen
        self.push_screen(FilePickerScreen(), self._on_file_selected)

    def _on_file_selected(self, selected_path: Path | None) -> None:
        """Callback when file is selected from modal."""
        if selected_path and selected_path.is_file():
            self.open_file(selected_path)

    def open_file(self, filepath: Path) -> None:
        """Switch current viewer to a new file."""
        try:
            new_content = filepath.read_text(encoding="utf-8")
            self.filepath = filepath
            self.SUB_TITLE = str(filepath.name)
            self.title = "mdreader"
            viewer = self.query_one("#viewer", MarkdownViewerWidget)
            viewer.update_content(new_content)
            
            # Restart file watcher on new file if in watch mode
            if self.watch:
                if self._watcher:
                    self._watcher.stop()
                self._watcher = FileWatcher(
                    filepath=self.filepath,
                    on_modified=self._on_file_changed,
                )
                self._watcher.start()
            self.notify(f"Opened: {filepath.name}", timeout=1.5)
        except Exception as e:
            self.notify(f"Failed to open file: {e}", title="Error", severity="error")

    def on_key(self, event) -> None:
        """Handle raw key sequences like 'gg' for scrolling to top."""
        if self.search_visible:
            return

        import time
        now = time.time()

        if event.character == "g":
            if now - self._last_g_press_time <= 0.5:
                self.action_scroll_home()
                self._last_g_press_time = 0.0
            else:
                self._last_g_press_time = now
        elif event.character == "G":
            self.action_scroll_end()
            self._last_g_press_time = 0.0
        else:
            self._last_g_press_time = 0.0

    def action_page_down(self) -> None:
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        viewer.page_down()

    def action_page_up(self) -> None:
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        viewer.page_up()

    def action_scroll_home(self) -> None:
        """Scroll to the top of the document (gg)."""
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        viewer.scroll_home()

    def action_scroll_end(self) -> None:
        """Scroll to the bottom of the document (G)."""
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        viewer.scroll_end()

    def action_scroll_down(self) -> None:
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        viewer.scroll_relative_custom(3)

    def action_scroll_up(self) -> None:
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        viewer.scroll_relative_custom(-3)
