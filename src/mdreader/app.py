"""Textual Application for Markdown Reader."""
import time
from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Input, Label
from textual.containers import Container, Vertical, Horizontal
from textual.reactive import reactive
from mdreader.widgets.markdown_view import MarkdownViewerWidget
from mdreader.utils.file_watcher import FileWatcher


class ClockLabel(Label):
    """Real-time clock display widget."""

    def on_mount(self) -> None:
        self.update_time()
        self.set_interval(1.0, self.update_time)

    def update_time(self) -> None:
        self.update(time.strftime("%X"))


class MDReaderApp(App):
    """Interactive TUI Markdown Reader Application."""

    ALLOW_SELECT = True
    ENABLE_SELECT_AUTO_SCROLL = True

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

    #footer-bar {
        dock: bottom;
        height: 1;
        width: 100%;
        background: $footer-background;
    }

    #footer-bar > Footer {
        width: 1fr;
        dock: none;
    }

    #footer-bar > Input {
        width: 1fr;
        height: 1;
        border: none;
        padding: 0 1;
        background: $surface;
        color: $text;
        display: none;
    }

    #footer-bar > Input.-visible {
        display: block;
    }

    #footer-bar.-searching > Footer {
        display: none;
    }

    #clock-label {
        width: auto;
        padding: 0 1;
        background: $footer-key-background;
        color: $footer-key-foreground;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("escape", "handle_escape", "Cancel/Back", show=False),
        Binding("t", "toggle_theme", "Theme", show=True),
        Binding("tab", "toggle_toc", "Outline (大綱)", show=True, priority=True),
        Binding("o", "open_file_picker", "Open File", show=True),
        Binding("v", "edit_in_editor", "Edit (Vim)", show=True),
        Binding("slash", "open_search", "Search", show=True),
        Binding("m", "toggle_mouse_mode", "Mouse Mode (滑鼠模式)", show=False),
        Binding("y", "copy_selected_text", "Yank / Copy", show=False),
        Binding("c", "copy_selected_text", "Copy", show=False),
        Binding("ctrl+c", "copy_selected_text", "Copy", show=False),
        Binding("ctrl+y", "copy_selected_text", "Yank", show=False),
        Binding("n", "search_next", "Next match", show=False),
        Binding("N", "search_prev", "Prev match", show=False),
        Binding("j", "page_up", "Page Up", show=False),
        Binding("k", "page_down", "Page Down", show=False),
        Binding("up", "scroll_up", "Up", show=False),
        Binding("down", "scroll_down", "Down", show=False),
        Binding("left", "scroll_left", "Left", show=False),
        Binding("right", "scroll_right", "Right", show=False),
        Binding("minus", "zoom_out", "Zoom Out (-)", show=False),
        Binding("equals", "zoom_in", "Zoom In (=)", show=False),
        Binding("plus", "zoom_in", "Zoom In (+)", show=False),
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
        self._search_query: str = ""
        self._search_matches: list[object] = []
        self._search_match_index: int = -1
        self._mouse_tracking_enabled: bool = True

        if self.filepath:
            self.SUB_TITLE = str(self.filepath.name)

    def compose(self) -> ComposeResult:
        with Container(id="main-container"):
            with Container(id="reader-box"):
                yield MarkdownViewerWidget(
                    raw_markdown=self.content,
                    show_toc=self.show_toc,
                    id="viewer",
                )
        with Horizontal(id="footer-bar"):
            yield Footer()
            yield Input(placeholder="/search pattern... (Enter to find, n: next, N: prev, Esc to dismiss)", id="search-input")
            yield ClockLabel(id="clock-label")

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

    def action_edit_in_editor(self) -> None:
        """Open current file in external editor ($EDITOR or vim) and reload upon exit."""
        import os
        import shutil
        import subprocess

        # If reading from stdin without filepath, prompt or notify
        if not self.filepath:
            self.notify("Cannot edit stdin/streamed content directly (no file path)", title="Edit", severity="warning")
            return

        editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "vim"
        editor_path = shutil.which(editor) or shutil.which("vim") or shutil.which("vi") or shutil.which("nano")
        if not editor_path:
            self.notify(f"Editor '{editor}' not found in PATH", title="Error", severity="error")
            return

        try:
            with self.suspend():
                subprocess.run([editor_path, str(self.filepath.resolve())])
            
            # Reload file content after returning from editor
            if self.filepath.exists():
                new_content = self.filepath.read_text(encoding="utf-8")
                viewer = self.query_one("#viewer", MarkdownViewerWidget)
                viewer.update_content(new_content)
                self.notify(f"Reloaded after editing: {self.filepath.name}", title="Edit", timeout=2)
        except Exception as e:
            self.notify(f"Error opening editor: {e}", title="Error", severity="error")

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
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        if target_block_id:
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
        """Open in-document search input in bottom footer bar."""
        footer_bar = self.query_one("#footer-bar")
        footer_bar.add_class("-searching")
        search_input = self.query_one("#search-input", Input)
        search_input.add_class("-visible")
        search_input.value = ""
        search_input.focus()
        self.search_visible = True

    def action_handle_escape(self) -> None:
        """Escape handles closing search input or quitting."""
        if self.search_visible:
            footer_bar = self.query_one("#footer-bar")
            footer_bar.remove_class("-searching")
            search_input = self.query_one("#search-input", Input)
            search_input.remove_class("-visible")
            viewer = self.query_one("#viewer", MarkdownViewerWidget)
            viewer.document.focus()
            self.search_visible = False
        else:
            self.exit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search submission (Vim-style /+keyword)."""
        if event.input.id == "search-input":
            query = event.value.strip()
            self.action_handle_escape()
            if query:
                self.perform_search(query)

    def perform_search(self, query: str) -> None:
        """Perform search in markdown content and jump to first match."""
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        matches = viewer.search_text(query)
        self._search_query = query
        self._search_matches = matches
        if not matches:
            self._search_match_index = -1
            self.notify(f"Pattern not found: {query}", title="Search", severity="warning", timeout=2)
            return

        self._search_match_index = 0
        viewer.scroll_to_block(matches[0])
        self.notify(f"[{1}/{len(matches)}] '{query}' (n: next, N: prev)", title="Search", timeout=2)

    def action_search_next(self) -> None:
        """Jump to next search match (n)."""
        if not self._search_matches:
            if self._search_query:
                self.perform_search(self._search_query)
            else:
                self.notify("No previous search pattern", title="Search", timeout=1.5)
            return
        
        self._search_match_index = (self._search_match_index + 1) % len(self._search_matches)
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        viewer.scroll_to_block(self._search_matches[self._search_match_index])
        idx = self._search_match_index + 1
        total = len(self._search_matches)
        self.notify(f"[{idx}/{total}] '{self._search_query}'", title="Search", timeout=1.5)

    def action_search_prev(self) -> None:
        """Jump to previous search match (N)."""
        if not self._search_matches:
            if self._search_query:
                self.perform_search(self._search_query)
            else:
                self.notify("No previous search pattern", title="Search", timeout=1.5)
            return
        
        self._search_match_index = (self._search_match_index - 1) % len(self._search_matches)
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        viewer.scroll_to_block(self._search_matches[self._search_match_index])
        idx = self._search_match_index + 1
        total = len(self._search_matches)
        self.notify(f"[{idx}/{total}] '{self._search_query}'", title="Search", timeout=1.5)

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

    def action_scroll_right(self) -> None:
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        viewer.scroll_horizontal(8)

    def action_scroll_left(self) -> None:
        viewer = self.query_one("#viewer", MarkdownViewerWidget)
        viewer.scroll_horizontal(-8)

    def action_zoom_in(self) -> None:
        """Enlarge reading column width (= / +). Use Cmd +/- for terminal font size."""
        reader_box = self.query_one("#reader-box")
        current_width = reader_box.styles.max_width
        screen_width = self.size.width

        if current_width is None:
            self.notify("版面寬度：滿版 (100%)\n💡 字型大小請用終端機原生快速鍵：Cmd + 或 Cmd -", title="版面寬度調整", timeout=2.5)
            return

        current_val = current_width.value if hasattr(current_width, "value") else int(current_width)
        new_val = current_val + 10
        if new_val >= screen_width:
            reader_box.styles.max_width = None
            self.max_width = None
            self.notify("版面寬度：滿版 (100%)\n💡 字型大小請用終端機原生快速鍵：Cmd + 或 Cmd -", title="版面寬度調整", timeout=2.5)
        else:
            reader_box.styles.max_width = new_val
            self.max_width = new_val
            self.notify(f"版面寬度：{new_val} 欄\n💡 字型大小請用終端機原生快速鍵：Cmd + 或 Cmd -", title="版面寬度調整", timeout=2.5)

    def action_zoom_out(self) -> None:
        """Narrow reading column width (-). Use Cmd +/- for terminal font size."""
        reader_box = self.query_one("#reader-box")
        current_width = reader_box.styles.max_width
        screen_width = self.size.width

        if current_width is None:
            current_val = screen_width
        else:
            current_val = current_width.value if hasattr(current_width, "value") else int(current_width)

        new_val = max(40, current_val - 10)
        reader_box.styles.max_width = new_val
        self.max_width = new_val
        self.notify(f"版面寬度：{new_val} 欄\n💡 字型大小請用終端機原生快速鍵：Cmd + 或 Cmd -", title="版面寬度調整", timeout=2.5)

    def copy_to_system_clipboard(self, text: str) -> bool:
        """Copy text to macOS/Linux system clipboard using native tools and OSC 52."""
        import subprocess
        success = False

        # 1. macOS pbcopy (native system clipboard)
        try:
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, close_fds=True)
            p.communicate(input=text.encode("utf-8"))
            if p.returncode == 0:
                success = True
        except Exception:
            pass

        # 2. Linux Wayland (wl-copy to both clipboard and primary selection)
        if not success:
            try:
                p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, close_fds=True)
                p.communicate(input=text.encode("utf-8"))
                if p.returncode == 0:
                    success = True
                    # Also write to primary selection for middle-click paste
                    subprocess.Popen(["wl-copy", "--primary"], stdin=subprocess.PIPE, close_fds=True).communicate(input=text.encode("utf-8"))
            except Exception:
                pass

        # 3. Linux X11 (xclip to both CLIPBOARD and PRIMARY selections)
        if not success:
            try:
                # Write to standard clipboard (Ctrl+V)
                p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, close_fds=True)
                p.communicate(input=text.encode("utf-8"))
                if p.returncode == 0:
                    success = True
                    # Also write to primary selection (mouse middle-click / highlight paste)
                    subprocess.Popen(["xclip", "-selection", "primary"], stdin=subprocess.PIPE, close_fds=True).communicate(input=text.encode("utf-8"))
            except Exception:
                pass

        # 4. Linux X11 (xsel fallback)
        if not success:
            try:
                p = subprocess.Popen(["xsel", "--clipboard", "--input"], stdin=subprocess.PIPE, close_fds=True)
                p.communicate(input=text.encode("utf-8"))
                if p.returncode == 0:
                    success = True
                    subprocess.Popen(["xsel", "--primary", "--input"], stdin=subprocess.PIPE, close_fds=True).communicate(input=text.encode("utf-8"))
            except Exception:
                pass

        # 5. Linux GNOME / GPaste fallback
        if not success:
            try:
                p = subprocess.Popen(["gpaste-client", "add"], stdin=subprocess.PIPE, close_fds=True)
                p.communicate(input=text.encode("utf-8"))
                if p.returncode == 0:
                    success = True
            except Exception:
                pass

        # 6. Textual built-in copy (OSC 52 escape code to terminal emulator)
        try:
            self.copy_to_clipboard(text)
            success = True
        except Exception:
            pass

        return success

    def action_copy_selected_text(self) -> None:
        """Copy current mouse-selected text to system clipboard (y / c / Ctrl+C)."""
        selected_text = self.screen.get_selected_text()
        if not selected_text or not selected_text.strip():
            self.notify("請先用滑鼠框選欲複製的文字", title="剪貼簿", timeout=1.5)
            return

        success = self.copy_to_system_clipboard(selected_text)
        preview = selected_text[:40].replace("\n", " ") + ("..." if len(selected_text) > 40 else "")
        if success:
            self.notify(f"已複製到剪貼簿：\n「{preview}」", title="複製成功", timeout=2.0)
        else:
            self.notify("無法寫入系統剪貼簿", title="複製失敗", severity="error", timeout=2.0)

    def on_text_selected(self, event) -> None:
        """Automatically copy when text is selected with mouse and notify."""
        selected_text = self.screen.get_selected_text()
        if selected_text and selected_text.strip():
            self.copy_to_system_clipboard(selected_text)
            preview = selected_text[:30].replace("\n", " ") + ("..." if len(selected_text) > 30 else "")
            self.notify(f"已自動複製：\n「{preview}」", title="剪貼簿", timeout=1.5)

    def on_mouse_down(self, event) -> None:
        """Right-click opens floating context menu for Copy / Search / Select All."""
        if event.button == 3:  # Right-click button
            event.stop()
            event.prevent_default()
            from mdreader.widgets.context_menu import ContextMenuModal
            selected_text = self.screen.get_selected_text()
            has_selection = bool(selected_text and selected_text.strip())
            self.push_screen(
                ContextMenuModal(x=event.screen_x, y=event.screen_y, has_selection=has_selection),
                self._on_context_menu_selected,
            )

    def _on_context_menu_selected(self, action: str | None) -> None:
        """Handle option selected from right-click context menu."""
        if not action:
            return

        if "Copy" in action:
            self.action_copy_selected_text()
        elif "Select All" in action:
            self.screen.text_select_all()
            self.notify("已全選文字 (可按 y 或右鍵複製)", title="全選", timeout=1.5)
        elif "Search" in action:
            selected_text = self.screen.get_selected_text()
            if selected_text and selected_text.strip():
                self.perform_search(selected_text.strip())
            else:
                self.action_open_search()

    def action_toggle_mouse_mode(self) -> None:
        """Toggle mouse tracking mode (m key). When disabled, terminal native selection is restored."""
        self._mouse_tracking_enabled = not self._mouse_tracking_enabled
        driver = self._driver
        if driver:
            if self._mouse_tracking_enabled:
                if hasattr(driver, "_enable_mouse_support"):
                    driver._enable_mouse_support()
                self.notify("滑鼠模式：已開啟 (TUI 滾輪與框選)\n💡 提示：按 m 可切換為終端原生模式", title="滑鼠模式 (m)", timeout=2.0)
            else:
                if hasattr(driver, "_disable_mouse_support"):
                    driver._disable_mouse_support()
                self.notify("滑鼠模式：已關閉 (恢復終端機原生反白與複製)\n💡 提示：現在可直接用滑鼠隨意反白文字", title="滑鼠模式 (m)", timeout=2.5)
