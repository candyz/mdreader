"""Textual Application for Markdown Reader."""
from __future__ import annotations
import os
import sys
import time
import subprocess
import webbrowser
import shutil
from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Input, Label
from textual.containers import Container, Vertical, Horizontal
from textual.reactive import reactive
from mdreader.widgets.markdown_view import MarkdownViewerWidget
from mdreader.widgets.virtual_viewer import VirtualTextViewer, should_use_virtual_viewer
from mdreader.widgets.link_picker import LinkPickerModal, extract_links_from_text
from mdreader.widgets.marks_modal import MarksModal
from mdreader.utils.file_watcher import FileWatcher
from mdreader.utils.config import get_config_value, set_config_value, add_recent_file
from mdreader.utils.mmap_buffer import MmapLineBuffer, MMAP_THRESHOLD_BYTES
from mdreader.widgets.commander import format_file_size
from mdreader.widgets.export_modal import ExportModal
from mdreader.widgets.code_block_modal import CodeBlockModal, extract_code_blocks
from mdreader.widgets.help_modal import ReaderHelpModal


class ClockLabel(Label):
    """Real-time clock display widget."""

    def on_mount(self) -> None:
        self.update_time()
        self.set_interval(1.0, self.update_time)

    def update_time(self) -> None:
        self.update(time.strftime("%X"))


class PositionLabel(Label):
    """Document scroll position and rich status indicator widget (like leaf/vim)."""

    def update_position(
        self,
        scroll_y: float,
        max_scroll_y: int,
        virtual_height: int = 0,
        size_height: int = 0,
        total_lines: int = 0,
        file_size: int | None = None,
        file_type: str | None = None,
        soft_wrap: bool = True,
        available_width: int = 120,
    ) -> None:
        if max_scroll_y <= 0:
            percent = 100 if virtual_height > 0 and virtual_height <= size_height else 0
        else:
            percent = int(round((scroll_y / max_scroll_y) * 100))
            percent = max(0, min(100, percent))

        if total_lines > 0:
            current_line = min(total_lines, max(1, int(round(scroll_y)) + 1))
            line_part = f"Ln {current_line}/{total_lines} ({percent}%)"
        else:
            line_part = f"{percent}%"

        parts: list[str] = []
        if file_size is not None and file_size > 0 and available_width >= 110:
            parts.append(format_file_size(file_size))
        if file_type and available_width >= 125:
            parts.append(file_type)
        if available_width >= 85:
            wrap_badge = r"\[WRAP]" if soft_wrap else r"\[NOWRAP]"
            parts.append(wrap_badge)
        parts.append(line_part)

        self.update(" │ ".join(parts))


class MDReaderApp(App):
    """Interactive TUI Markdown Reader Application."""

    ALLOW_SELECT = True
    ENABLE_SELECT_AUTO_SCROLL = True
    ENABLE_COMMAND_PALETTE = False

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

    #cmd-prompt-bar {
        height: 1;
        width: 100%;
        background: $surface-darken-1;
        display: none;
        padding: 0 1;
    }

    #cmd-prompt-bar.-visible {
        display: block;
    }

    #prompt-label {
        width: auto;
        color: $success;
        text-style: bold;
        margin-right: 1;
    }

    #prompt-input {
        width: 1fr;
        height: 1;
        border: none;
        padding: 0;
        background: transparent;
        color: $text;
    }

    #position-label {
        width: auto;
        padding: 0 1;
        background: $footer-key-background;
        color: $footer-key-foreground;
        text-style: bold;
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
        Binding("o", "open_file_picker", "Open", show=True),
        Binding("O", "toggle_toc", "Outline", show=True),
        Binding("ctrl+o", "open_commander", "Commander", show=True),
        Binding("w", "toggle_wrap", "Wrap", show=True),
        Binding("v", "edit_in_editor", "Edit", show=True),
        Binding("t", "toggle_theme", "Theme", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("h", "open_help", "Help", show=True),
        Binding("question_mark", "open_help", "Help (?)", show=False),
        Binding("f1", "open_help", "Help (F1)", show=False),
        Binding("escape", "handle_escape", "Cancel/Back", show=False),
        Binding("slash", "open_search", "Search (/)", show=False),
        Binding("colon", "open_goto_line", "Go to Line (:)", show=False),
        Binding("alt+z", "toggle_wrap", "Wrap (Alt+Z)", show=False),
        Binding("gx", "open_link", "Open Link (gx)", show=False),
        Binding("ctrl+m", "list_marks", "Marks (Ctrl+M)", show=False),
        Binding("m", "toggle_mouse_mode", "Mouse Mode (滑鼠模式)", show=False),
        Binding("T", "toggle_cmd_prompt", "Terminal Prompt (T)", show=False),
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
        Binding("d", "scroll_left", "Scroll Left (d)", show=False),
        Binding("f", "scroll_right", "Scroll Right (f)", show=False),
        Binding("minus", "zoom_out", "Zoom Out (-)", show=False),
        Binding("equals", "zoom_in", "Zoom In (=)", show=False),
        Binding("plus", "zoom_in", "Zoom In (+)", show=False),
        Binding("e", "export_document", "Export (e)", show=False),
        Binding("Y", "copy_code_block", "Copy Code (Y)", show=False),
        Binding("ctrl+k", "copy_code_block", "Copy Code", show=False),
        Binding("ctrl+t", "open_in_terminal", "Terminal (Ctrl+T)", show=False),
        Binding("ctrl+shift+o", "reveal_in_finder", "Reveal File", show=False),
        Binding("L", "toggle_line_numbers", "Line No (L)", show=False),
        Binding("alt+l", "toggle_line_numbers", "Line No", show=False),
        Binding("G", "scroll_end", "Scroll End (Bottom)", show=False),
        Binding("r", "reload_file", "Reload", show=False),
    ]

    search_visible = reactive(False)
    cmd_prompt_visible = reactive(False)

    def __init__(
        self,
        content: str = "",
        filepath: Path | str | None = None,
        max_width: int | None = None,
        watch: bool = False,
        theme: str | None = None,
        show_toc: bool = False,
        initial_line: int | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.filepath = Path(filepath) if filepath else None
        self.initial_line = initial_line
        self._mmap_buffer: MmapLineBuffer | None = None
        if not content and self.filepath and self.filepath.is_file():
            try:
                fname = self.filepath.name
                if self.filepath.stat().st_size > MMAP_THRESHOLD_BYTES and should_use_virtual_viewer("", fname):
                    self._mmap_buffer = MmapLineBuffer(self.filepath)
                    self.content = ""
                else:
                    self.content = self.filepath.read_text(encoding="utf-8")
            except Exception:
                self.content = content
        else:
            self.content = content
        self.max_width = max_width
        self.watch_mode = watch
        self.show_toc = show_toc
        self._custom_theme = theme
        self._theme_index = 0
        self._watcher: FileWatcher | None = None
        self._last_g_press_time: float = 0.0
        self._search_query: str = ""
        self._search_matches: list[object] = []
        self._search_match_index: int = -1
        self._mouse_tracking_enabled: bool = True
        self._digit_buffer: str = ""
        self._input_mode: str = "search"
        self._soft_wrap: bool = True
        self._marks: dict[str, int] = {}
        self._waiting_for_mark: bool = False
        self._waiting_for_jump_mark: bool = False

        if self.filepath:
            self.SUB_TITLE = str(self.filepath.name)

    def _create_viewer(self, content: str = "", filename: str | None = None):
        """Create high-performance VirtualTextViewer for large/code files or MarkdownViewerWidget for rich markdown."""
        if should_use_virtual_viewer(content, filename):
            if getattr(self, "_mmap_buffer", None) is not None:
                return VirtualTextViewer(lines=self._mmap_buffer, filename=filename, id="viewer")
            return VirtualTextViewer(raw_text=content, filename=filename, id="viewer")
        return MarkdownViewerWidget(
            raw_markdown=content,
            show_toc=self.show_toc,
            filename=filename,
            id="viewer",
        )

    def compose(self) -> ComposeResult:
        with Container(id="main-container"):
            with Container(id="reader-box"):
                yield self._create_viewer(
                    content=self.content,
                    filename=str(self.filepath.name) if self.filepath else None,
                )
        with Horizontal(id="cmd-prompt-bar"):
            yield Label(self._get_prompt_label(), id="prompt-label")
            yield Input(placeholder="Type shell command (e.g. ls, git status, cd <dir>)... Enter to run, Esc to close", id="prompt-input")
        with Horizontal(id="footer-bar"):
            yield Footer()
            yield Input(placeholder="/search pattern... (Enter to find, n: next, N: prev, Esc to dismiss)", id="search-input")
            yield PositionLabel("0%", id="position-label")
            yield ClockLabel(id="clock-label")

    def _get_prompt_label(self) -> str:
        """Generate Midnight Commander style command line prompt [user@host:dir]$."""
        import getpass, socket
        try:
            user = getpass.getuser()
        except Exception:
            user = "user"
        try:
            host = socket.gethostname().split(".")[0]
        except Exception:
            host = "host"
        try:
            cwd = str(self.filepath.parent if self.filepath and self.filepath.exists() else Path.cwd())
            home = str(Path.home())
            if cwd.startswith(home):
                cwd = "~" + cwd[len(home):]
        except Exception:
            cwd = "."
        return f"[{user}@{host}:{cwd}]$"

    def watch_cmd_prompt_visible(self, visible: bool) -> None:
        try:
            bar = self.query_one("#cmd-prompt-bar", Horizontal)
            inp = self.query_one("#prompt-input", Input)
            lbl = self.query_one("#prompt-label", Label)
            if visible:
                lbl.update(self._get_prompt_label())
                bar.add_class("-visible")
                inp.value = ""
                inp.focus()
            else:
                bar.remove_class("-visible")
                viewer = self.query_one("#viewer")
                if hasattr(viewer, "document") and viewer.document:
                    viewer.document.focus()
                else:
                    viewer.focus()
        except Exception:
            pass

    def action_toggle_cmd_prompt(self) -> None:
        """Toggle Midnight Commander style Terminal Prompt bar (T)."""
        self.cmd_prompt_visible = not self.cmd_prompt_visible

    def on_mount(self) -> None:
        if self.max_width:
            reader_box = self.query_one("#reader-box")
            reader_box.styles.max_width = self.max_width

        if self._custom_theme:
            if self._custom_theme in self.available_themes:
                self.theme = self._custom_theme
        else:
            saved_theme = get_config_value("theme")
            if saved_theme and saved_theme in self.available_themes:
                self.theme = saved_theme
        
        # Sync _theme_index with current theme
        valid_themes = [t for t in self.THEME_LIST if t in self.available_themes]
        if self.theme in valid_themes:
            self._theme_index = valid_themes.index(self.theme)
        
        # Ensure focus is on markdown document for immediate keyboard response
        viewer = self.query_one("#viewer")
        if hasattr(viewer, "document"):
            viewer.document.focus()
        else:
            viewer.focus()
        self.watch(viewer, "scroll_y", self._update_position_label)
        self.watch(viewer, "max_scroll_y", self._update_position_label)

        # Record opened file to recent files history
        if self.filepath:
            add_recent_file(self.filepath)

        # Jump to initial line if requested via CLI
        if self.initial_line is not None:
            self.action_goto_line(self.initial_line)

        # Start file watcher if watch mode is enabled
        if self.watch_mode and self.filepath and self.filepath.exists():
            self._watcher = FileWatcher(
                filepath=self.filepath,
                on_modified=self._on_file_changed,
            )
            self._watcher.start()

    def on_resize(self, event) -> None:
        """Responsive layout adjustment on window resize."""
        try:
            clock = self.query_one("#clock-label")
            if event.size.width < 95:
                clock.styles.display = "none"
            else:
                clock.styles.display = "block"
        except Exception:
            pass
        self._update_position_label()

    def _update_position_label(self) -> None:
        """Update reading progress percentage and rich status bar label."""
        try:
            viewer = self.query_one("#viewer")
            pos_label = self.query_one("#position-label", PositionLabel)

            if hasattr(viewer, "lines"):
                total_lines = len(viewer.lines)
            elif hasattr(viewer, "raw_markdown"):
                total_lines = len(viewer.raw_markdown.splitlines())
            else:
                total_lines = viewer.virtual_size.height

            file_size = None
            file_type = None
            if self.filepath and self.filepath.exists():
                try:
                    file_size = self.filepath.stat().st_size
                    ext = self.filepath.suffix.lower()
                    if ext in (".md", ".markdown"):
                        file_type = "Markdown"
                    elif ext in (".py",):
                        file_type = "Python"
                    elif ext in (".rs",):
                        file_type = "Rust"
                    elif ext in (".c", ".h", ".cpp"):
                        file_type = "C/C++"
                    elif ext in (".html", ".htm"):
                        file_type = "HTML"
                    elif ext in (".json", ".toml", ".yaml", ".yml"):
                        file_type = "Data"
                    else:
                        file_type = "Text"
                except Exception:
                    pass

            screen_w = self.size.width if self.size and self.size.width > 0 else 120
            # Responsive clock hiding when screen is narrow (< 95 cols)
            try:
                clock = self.query_one("#clock-label")
                if screen_w < 95:
                    clock.styles.display = "none"
                else:
                    clock.styles.display = "block"
            except Exception:
                pass

            pos_label.update_position(
                scroll_y=viewer.scroll_y,
                max_scroll_y=viewer.max_scroll_y,
                virtual_height=viewer.virtual_size.height,
                size_height=viewer.size.height,
                total_lines=total_lines,
                file_size=file_size,
                file_type=file_type,
                soft_wrap=self._soft_wrap,
                available_width=screen_w,
            )
        except Exception:
            pass

    def on_unmount(self) -> None:
        if self._watcher:
            self._watcher.stop()
            self._watcher = None

    def _on_file_changed(self) -> None:
        """Invoked in background thread by FileWatcher."""
        self.call_from_thread(lambda: self.run_worker(self.action_reload_file()))

    async def action_reload_file(self) -> None:
        """Reload file content from disk and update viewer."""
        if self.filepath and self.filepath.exists():
            try:
                new_content = self.filepath.read_text(encoding="utf-8")
                fname = str(self.filepath.name)
                viewer = self.query_one("#viewer")
                use_virtual = should_use_virtual_viewer(new_content, fname)
                is_currently_virtual = isinstance(viewer, VirtualTextViewer)

                if use_virtual == is_currently_virtual:
                    viewer.update_content(new_content, fname)
                else:
                    reader_box = self.query_one("#reader-box", Container)
                    await reader_box.remove_children()
                    new_viewer = self._create_viewer(new_content, fname)
                    await reader_box.mount(new_viewer)
                    if hasattr(new_viewer, "document"):
                        new_viewer.document.focus()
                    else:
                        new_viewer.focus()
                    self.watch(new_viewer, "scroll_y", self._update_position_label)
                    self.watch(new_viewer, "max_scroll_y", self._update_position_label)

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
                viewer = self.query_one("#viewer")
                viewer.update_content(new_content, str(self.filepath.name))
                self.notify(f"Reloaded after editing: {self.filepath.name}", title="Edit", timeout=2)
        except Exception as e:
            self.notify(f"Error opening editor: {e}", title="Error", severity="error")

    def action_toggle_toc(self) -> None:
        """Open full outline modal for chapter browsing and jumping."""
        from mdreader.widgets.outline_modal import OutlineModalScreen
        viewer = self.query_one("#viewer")
        headings = viewer.get_headings()
        if not headings:
            self.notify("No headings found in document", title="Outline", timeout=1.5)
            return
        self.push_screen(OutlineModalScreen(headings), self._on_outline_selected)

    def _on_outline_selected(self, target_block_id: str | None) -> None:
        """Callback when a heading is selected from Outline modal."""
        viewer = self.query_one("#viewer")
        if target_block_id:
            viewer.scroll_to_heading_id(target_block_id)
        if hasattr(viewer, "document"):
            viewer.document.focus()
        else:
            viewer.focus()

    def action_toggle_theme(self) -> None:
        """Cycle through available color themes."""
        # Find next valid theme
        valid_themes = [t for t in self.THEME_LIST if t in self.available_themes]
        if not valid_themes:
            return
        self._theme_index = (self._theme_index + 1) % len(valid_themes)
        new_theme = valid_themes[self._theme_index]
        self.theme = new_theme
        set_config_value("theme", new_theme)
        self.notify(f"Theme switched to: {new_theme}", timeout=1.5)

    def action_open_search(self) -> None:
        """Open in-document search input in bottom footer bar."""
        footer_bar = self.query_one("#footer-bar")
        footer_bar.add_class("-searching")
        search_input = self.query_one("#search-input", Input)
        search_input.placeholder = "/search pattern... (Enter to find, n: next, N: prev, Esc to dismiss)"
        search_input.value = ""
        search_input.add_class("-visible")
        search_input.focus()
        self.search_visible = True
        self._input_mode = "search"

    def action_open_goto_line(self) -> None:
        """Open jump to line number input in bottom footer bar."""
        footer_bar = self.query_one("#footer-bar")
        footer_bar.add_class("-searching")
        search_input = self.query_one("#search-input", Input)
        search_input.placeholder = ":line number... (Enter to jump, e.g. 42 or 100, Esc to dismiss)"
        search_input.value = ":"
        search_input.add_class("-visible")
        search_input.focus()
        self.search_visible = True
        self._input_mode = "goto"

    def action_handle_escape(self) -> None:
        """Escape handles closing prompt, search input or quitting."""
        if self.cmd_prompt_visible:
            self.cmd_prompt_visible = False
            return
        if self.search_visible:
            footer_bar = self.query_one("#footer-bar")
            footer_bar.remove_class("-searching")
            search_input = self.query_one("#search-input", Input)
            search_input.remove_class("-visible")
            viewer = self.query_one("#viewer")
            if hasattr(viewer, "document"):
                viewer.document.focus()
            else:
                viewer.focus()
            self.search_visible = False
        else:
            self.exit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search, goto line, or terminal command prompt submission."""
        if event.input.id == "search-input":
            val = event.value.strip()
            self.action_handle_escape()
            if not val:
                return
            if val.startswith(":") or self._input_mode == "goto":
                num_str = val.lstrip(":").strip()
                if num_str.isdigit():
                    self.action_goto_line(int(num_str))
                else:
                    self.notify(f"Invalid line number: {val}", title="Go to Line", severity="warning", timeout=2)
            else:
                self.perform_search(val)
        elif event.input.id == "prompt-input":
            cmd = event.value.strip()
            if cmd:
                self._execute_terminal_command(cmd)
            else:
                self.cmd_prompt_visible = False

    def _execute_terminal_command(self, cmd: str) -> None:
        """Execute a shell command in current file/working directory and refresh UI."""
        target_dir = self.filepath.parent if self.filepath and self.filepath.exists() else Path.cwd()
        if cmd.startswith("cd ") or cmd == "cd":
            parts = cmd.split(maxsplit=1)
            target = parts[1] if len(parts) > 1 else str(Path.home())
            target_path = Path(os.path.expanduser(target))
            if not target_path.is_absolute():
                target_path = (target_dir / target_path).resolve()
            if target_path.is_dir():
                os.chdir(target_path)
                self.notify(f"已切換目錄至：{target_path}", title="cd", timeout=2.0)
            else:
                self.notify(f"找不到目錄：{target}", title="Error", severity="error")
            lbl = self.query_one("#prompt-label", Label)
            lbl.update(self._get_prompt_label())
            inp = self.query_one("#prompt-input", Input)
            inp.value = ""
            return

        try:
            with self.suspend():
                print(f"\033[1;32m{self._get_prompt_label()} {cmd}\033[0m\n")
                subprocess.run(cmd, shell=True, cwd=str(target_dir.resolve()))
                print("\n\033[1;34m[Press Enter to return to mdreader]\033[0m", end="")
                sys.stdout.flush()
                input()
        except Exception as e:
            self.notify(f"執行指令失敗：{e}", title="Error", severity="error")

        try:
            inp = self.query_one("#prompt-input", Input)
            inp.value = ""
            lbl = self.query_one("#prompt-label", Label)
            lbl.update(self._get_prompt_label())
        except Exception:
            pass

    def action_goto_line(self, line_number: int) -> None:
        """Jump to specific line number in document (1-indexed)."""
        viewer = self.query_one("#viewer")
        if isinstance(viewer, VirtualTextViewer):
            total_lines = max(1, len(viewer.lines))
            target_line = max(1, min(total_lines, line_number))
            target_idx = target_line - 1
            viewer.scroll_to_block(target_idx)
            viewer.scroll_to(y=target_idx, animate=False)
            self.notify(f"Jumped to line {target_line}/{total_lines}", title="Go to Line", timeout=1.5)
        else:
            if hasattr(viewer, "raw_markdown"):
                total_lines = max(1, len(viewer.raw_markdown.splitlines()))
            else:
                total_lines = max(1, viewer.virtual_size.height)
            target_line = max(1, min(total_lines, line_number))
            if total_lines > 1 and viewer.max_scroll_y > 0:
                target_y = int(round((target_line - 1) / (total_lines - 1) * viewer.max_scroll_y))
            else:
                target_y = 0
            viewer.scroll_to(y=target_y, animate=False)
            self.notify(f"Jumped to line {target_line}/{total_lines}", title="Go to Line", timeout=1.5)

    def perform_search(self, query: str) -> None:
        """Perform search in markdown content and jump to first match."""
        viewer = self.query_one("#viewer")
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
        viewer = self.query_one("#viewer")
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
        viewer = self.query_one("#viewer")
        viewer.scroll_to_block(self._search_matches[self._search_match_index])
        idx = self._search_match_index + 1
        total = len(self._search_matches)
        self.notify(f"[{idx}/{total}] '{self._search_query}'", title="Search", timeout=1.5)

    def action_open_file_picker(self) -> None:
        """Open fuzzy file picker modal."""
        from mdreader.widgets.file_picker import FilePickerScreen
        start_dir = self.filepath.parent if self.filepath and self.filepath.exists() else Path.cwd()
        self.push_screen(FilePickerScreen(start_dir=start_dir), self._on_file_selected)

    def action_open_commander(self) -> None:
        """Toggle Midnight Commander-style dual pane file manager mode (F9 / Ctrl+O)."""
        from mdreader.widgets.commander import CommanderScreen
        self.push_screen(CommanderScreen(current_path=self.filepath), self._on_file_selected)

    def _on_file_selected(self, selected_result: Path | tuple[Path, int] | None) -> None:
        """Callback when file is selected from modal (supports Path or (Path, line_no))."""
        if isinstance(selected_result, tuple):
            filepath, line_no = selected_result
            if filepath.is_file():
                self.run_worker(self.open_file(filepath, line_no=line_no))
        elif isinstance(selected_result, Path) and selected_result.is_file():
            self.run_worker(self.open_file(selected_result))

    async def open_file(self, filepath: Path, line_no: int | None = None) -> None:
        """Switch current viewer to a new file and optionally jump to a line number."""
        try:
            self.filepath = filepath
            self.SUB_TITLE = str(filepath.name)
            self.title = "mdreader"
            add_recent_file(filepath)
            fname = str(filepath.name)

            is_large_mmap = filepath.stat().st_size > MMAP_THRESHOLD_BYTES and should_use_virtual_viewer("", fname)
            if is_large_mmap:
                if hasattr(self, "_mmap_buffer") and self._mmap_buffer:
                    self._mmap_buffer.close()
                self._mmap_buffer = MmapLineBuffer(filepath)
                new_content = ""
            else:
                if hasattr(self, "_mmap_buffer") and self._mmap_buffer:
                    self._mmap_buffer.close()
                    self._mmap_buffer = None
                new_content = filepath.read_text(encoding="utf-8")

            self.content = new_content
            use_virtual = is_large_mmap or should_use_virtual_viewer(new_content, fname)
            current_viewer = self.query_one("#viewer")
            is_currently_virtual = isinstance(current_viewer, VirtualTextViewer)

            if use_virtual and is_currently_virtual:
                if is_large_mmap:
                    current_viewer.update_content(self._mmap_buffer, fname)
                else:
                    current_viewer.update_content(new_content, fname)
            else:
                reader_box = self.query_one("#reader-box", Container)
                await reader_box.remove_children()
                new_viewer = self._create_viewer(new_content, fname)
                await reader_box.mount(new_viewer)
                if hasattr(new_viewer, "document"):
                    new_viewer.document.focus()
                else:
                    new_viewer.focus()
                self.watch(new_viewer, "scroll_y", self._update_position_label)
                self.watch(new_viewer, "max_scroll_y", self._update_position_label)

            # Restart file watcher on new file if in watch mode
            if self.watch_mode:
                if self._watcher:
                    self._watcher.stop()
                self._watcher = FileWatcher(
                    filepath=self.filepath,
                    on_modified=self._on_file_changed,
                )
                self._watcher.start()

            if line_no is not None:
                self.action_goto_line(line_no)

            self.notify(f"Opened: {filepath.name}", timeout=1.5)
        except Exception as e:
            self.notify(f"Failed to open file: {e}", title="Error", severity="error")

    def _get_current_line(self) -> int:
        """Get the line number currently at the top of the viewport (1-indexed)."""
        try:
            viewer = self.query_one("#viewer")
            scroll_y = int(viewer.scroll_y)
            return max(1, scroll_y + 1)
        except Exception:
            return 1

    def action_toggle_wrap(self) -> None:
        """Toggle soft line wrapping on/off (w / Alt+Z)."""
        self._soft_wrap = not self._soft_wrap
        viewer = self.query_one("#viewer")
        if hasattr(viewer, "set_soft_wrap"):
            viewer.set_soft_wrap(self._soft_wrap)
        status_text = "已開啟 (Wrap)" if self._soft_wrap else "已關閉 (No Wrap, 可按 h/l 水平捲動)"
        self.notify(f"自動折行：{status_text}", title="自動換行 (w)", timeout=1.5)

    def action_toggle_line_numbers(self) -> None:
        """Toggle line numbers visibility in VirtualTextViewer (L / Alt+L)."""
        viewer = self.query_one("#viewer")
        if hasattr(viewer, "toggle_line_numbers"):
            state = viewer.toggle_line_numbers()
            msg = "已顯示行號 (Line Numbers On)" if state else "已隱藏行號 (Line Numbers Off)"
            self.notify(msg, title="行號切換 (L)", timeout=1.5)
        else:
            self.notify("Markdown 渲染模式不支援行號切換（僅純文字/原始碼模式支援）", title="行號切換 (L)", timeout=2.0)

    def action_open_help(self) -> None:
        """Open full keyboard shortcuts & help guide modal (h / ? / F1)."""
        self.push_screen(ReaderHelpModal())

    def action_open_link(self) -> None:
        """Extract hyperlinks from document and open in browser (gx)."""
        doc_text = self._mmap_buffer.read_all_text() if getattr(self, "_mmap_buffer", None) is not None else (self.content or "")
        links = extract_links_from_text(doc_text)
        if not links:
            self.notify("文件中未發現任何超連結 (HTTP/HTTPS)", title="開啟超連結 (gx)", severity="warning", timeout=2.0)
            return
        if len(links) == 1:
            import webbrowser
            url = links[0][1]
            try:
                webbrowser.open(url)
            except Exception:
                pass
            self.notify(f"已在瀏覽器開啟：\n{url}", title="開啟超連結 (gx)", timeout=2.0)
            return

        self.push_screen(LinkPickerModal(links), self._on_link_picked)

    def _on_link_picked(self, url: str | None) -> None:
        if url:
            self.notify(f"已在瀏覽器開啟：\n{url}", title="開啟超連結 (gx)", timeout=2.0)

    def action_export_document(self) -> None:
        """Export document to HTML, TXT, or MD format (e)."""
        doc_text = self._mmap_buffer.read_all_text() if getattr(self, "_mmap_buffer", None) is not None else (self.content or "")
        if not doc_text.strip():
            self.notify("目前沒有可匯出的文件內容", title="匯出 (e)", severity="warning", timeout=2.0)
            return
        self.push_screen(ExportModal(content=doc_text, current_filepath=self.filepath), self._on_export_complete)

    def _on_export_complete(self, exported_path: Path | None) -> None:
        if exported_path and exported_path.exists():
            self.notify(f"已成功匯出至：\n{exported_path}", title="匯出成功", timeout=3.0)

    def action_copy_code_block(self) -> None:
        """Extract and copy fenced code blocks from markdown (Y / Ctrl+K)."""
        doc_text = self._mmap_buffer.read_all_text() if getattr(self, "_mmap_buffer", None) is not None else (self.content or "")
        blocks = extract_code_blocks(doc_text)
        if not blocks:
            self.notify("文件中未發現任何程式碼區塊 (Code Blocks)", title="複製程式碼 (Y)", severity="warning", timeout=2.0)
            return
        if len(blocks) == 1:
            code = blocks[0][1]
            self.copy_to_system_clipboard(code)
            self.notify(f"已複製程式碼區塊 ({len(code.splitlines())} 行)", title="複製程式碼成功 (Y)", timeout=2.0)
            return

        self.push_screen(CodeBlockModal(blocks), self._on_code_block_selected)

    def _on_code_block_selected(self, code: str | None) -> None:
        if code:
            self.copy_to_system_clipboard(code)
            self.notify(f"已複製程式碼區塊 ({len(code.splitlines())} 行)", title="複製程式碼成功", timeout=2.0)

    def action_open_in_terminal(self) -> None:
        """Launch terminal shell in current file directory (Ctrl+T)."""
        target_dir = self.filepath.parent if self.filepath and self.filepath.exists() else Path.cwd()
        shell = os.environ.get("SHELL") or "/bin/sh"
        try:
            with self.suspend():
                import subprocess
                subprocess.run([shell], cwd=str(target_dir.resolve()))
        except Exception as e:
            self.notify(f"無法開啟終端機：{e}", title="Error", severity="error")

    def action_reveal_in_finder(self) -> None:
        """Reveal file or folder in system file manager (Finder / xdg-open)."""
        target_path = self.filepath if self.filepath and self.filepath.exists() else Path.cwd()
        import subprocess, sys
        try:
            if sys.platform == "darwin":
                if target_path.is_file():
                    subprocess.run(["open", "-R", str(target_path)])
                else:
                    subprocess.run(["open", str(target_path)])
            elif sys.platform.startswith("linux"):
                subprocess.run(["xdg-open", str(target_path.parent if target_path.is_file() else target_path)])
            self.notify(f"已在檔案管理員中顯示：\n{target_path.name}", title="檔案管理員", timeout=2.0)
        except Exception as e:
            self.notify(f"無法開啟檔案管理員：{e}", title="Error", severity="error")

    def action_list_marks(self) -> None:
        """Open bookmarks modal dialog (Ctrl+M)."""
        lines = self.content.splitlines() if self.content else []
        self.push_screen(MarksModal(self._marks, lines), self._on_mark_selected)

    def _on_mark_selected(self, target_line: int | None) -> None:
        if target_line is not None:
            self.action_goto_line(target_line)

    def on_key(self, event) -> None:
        """Handle raw key sequences like 'gg', 'G', '123G', 'm[a-z]', and '[a-z]' for marks/jumps."""
        if self.search_visible:
            return

        import time
        now = time.time()

        # 1. Handle setting mark after 'm' key
        if self._waiting_for_mark:
            self._waiting_for_mark = False
            if event.character and event.character.isalpha():
                key = event.character.lower()
                line_no = self._get_current_line()
                self._marks[key] = line_no
                self.notify(f"已在第 {line_no} 行設定書籤 [{key.upper()}]", title="設定書籤 (Mark)", timeout=1.5)
                return

        # 2. Handle jumping to mark after "'" or "`" key
        if self._waiting_for_jump_mark:
            self._waiting_for_jump_mark = False
            if event.character and event.character.isalpha():
                key = event.character.lower()
                if key in self._marks:
                    line_no = self._marks[key]
                    self.action_goto_line(line_no)
                    self.notify(f"已跳轉至書籤 [{key.upper()}] (第 {line_no} 行)", title="跳轉書籤", timeout=1.5)
                else:
                    self.notify(f"未設定書籤 [{key.upper()}]", title="書籤不存在", severity="warning", timeout=1.5)
                return

        # 3. Digit buffering for numeric line jump
        if event.character and event.character.isdigit():
            self._digit_buffer += event.character
            return

        # 4. Handle mark prefix keys 'm' and "'"
        if event.character == "m":
            self._waiting_for_mark = True
            return
        elif event.character in ("'", "`"):
            self._waiting_for_jump_mark = True
            return

        # 5. Handle navigation and jumps
        if event.character == "g":
            if self._digit_buffer:
                target_line = int(self._digit_buffer)
                self._digit_buffer = ""
                self._last_g_press_time = 0.0
                self.action_goto_line(target_line)
            elif now - self._last_g_press_time <= 0.5:
                self.action_scroll_home()
                self._last_g_press_time = 0.0
            else:
                self._last_g_press_time = now
        elif event.character == "G":
            if self._digit_buffer:
                target_line = int(self._digit_buffer)
                self._digit_buffer = ""
                self.action_goto_line(target_line)
            else:
                self.action_scroll_end()
            self._last_g_press_time = 0.0
        elif event.character == ":":
            self._digit_buffer = ""
            self.action_open_goto_line()
        else:
            self._digit_buffer = ""
            self._last_g_press_time = 0.0

    def action_page_down(self) -> None:
        viewer = self.query_one("#viewer")
        viewer.page_down()

    def action_page_up(self) -> None:
        viewer = self.query_one("#viewer")
        viewer.page_up()

    def action_scroll_home(self) -> None:
        """Scroll to the top of the document (gg)."""
        viewer = self.query_one("#viewer")
        viewer.scroll_home()

    def action_scroll_end(self) -> None:
        """Scroll to the bottom of the document (G)."""
        viewer = self.query_one("#viewer")
        viewer.scroll_end()

    def action_scroll_down(self) -> None:
        viewer = self.query_one("#viewer")
        viewer.scroll_relative_custom(3)

    def action_scroll_up(self) -> None:
        viewer = self.query_one("#viewer")
        viewer.scroll_relative_custom(-3)

    def action_scroll_right(self) -> None:
        viewer = self.query_one("#viewer")
        viewer.scroll_horizontal(8)

    def action_scroll_left(self) -> None:
        viewer = self.query_one("#viewer")
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
        """Copy mouse-selected text or full document to system clipboard (y / c / Ctrl+C)."""
        selected_text = self.screen.get_selected_text()
        if selected_text and selected_text.strip():
            success = self.copy_to_system_clipboard(selected_text)
            preview = selected_text[:40].replace("\n", " ") + ("..." if len(selected_text) > 40 else "")
            if success:
                self.notify(f"已複製選取文字：\n「{preview}」", title="複製成功", timeout=2.0)
            else:
                self.notify("無法寫入系統剪貼簿", title="複製失敗", severity="error", timeout=2.0)
            return

        # If no text selected with mouse, copy the whole document content
        if getattr(self, "_mmap_buffer", None) is not None:
            doc_text = self._mmap_buffer.read_all_text()
        else:
            doc_text = self.content
        if doc_text and doc_text.strip():
            success = self.copy_to_system_clipboard(doc_text)
            lines_count = doc_text.count("\n") + 1
            if success:
                self.notify(f"已複製全文至剪貼簿 ({lines_count} 行 / {len(doc_text)} 字元)", title="全文複製成功 (y)", timeout=2.0)
            else:
                self.notify("無法寫入系統剪貼簿", title="複製失敗", severity="error", timeout=2.0)
        else:
            self.notify("目前沒有可複製的內容", title="剪貼簿", timeout=1.5)

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
