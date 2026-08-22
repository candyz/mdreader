"""Midnight Commander-style dual-pane file manager screen for mdreader."""
from __future__ import annotations
import os
import sys
import shutil
from pathlib import Path
from typing import List, Optional, Tuple, Set
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import Screen, ModalScreen
from textual.widgets import OptionList, Label, Footer, Input, Button
from textual.widgets.option_list import Option
from textual.binding import Binding
from textual import events
from mdreader.utils.config import get_config_value, set_config_value


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes into human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}K"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}M"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f}G"


class PromptModal(ModalScreen[Optional[str]]):
    """Modal screen for single-line text input (Mkdir, Rename, Target path)."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
    ]

    CSS = """
    PromptModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #prompt-dialog {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    #prompt-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #prompt-input {
        width: 100%;
        margin-bottom: 1;
    }
    #prompt-buttons {
        width: 100%;
        height: 3;
        align: right middle;
    }
    #prompt-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, title: str, initial_value: str = "", placeholder: str = ""):
        super().__init__()
        self.prompt_title = title
        self.initial_value = initial_value
        self.placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Vertical(id="prompt-dialog"):
            yield Label(self.prompt_title, id="prompt-title")
            yield Input(value=self.initial_value, placeholder=self.placeholder, id="prompt-input")
            with Horizontal(id="prompt-buttons"):
                yield Button("Cancel (Esc)", variant="default", id="btn-cancel")
                yield Button("OK (Enter)", variant="primary", id="btn-ok")

    def on_mount(self) -> None:
        self.query_one("#prompt-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()
        self.dismiss(val if val else None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-ok":
            val = self.query_one("#prompt-input", Input).value.strip()
            self.dismiss(val if val else None)
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class ConfirmModal(ModalScreen[bool]):
    """Modal screen for confirming destructive operations (Delete, Overwrite)."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
        Binding("y", "confirm", "Yes", priority=True),
        Binding("n", "cancel", "No", priority=True),
    ]

    CSS = """
    ConfirmModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #confirm-dialog {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $error;
        padding: 1 2;
    }
    #confirm-title {
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }
    #confirm-msg {
        margin-bottom: 1;
    }
    #confirm-buttons {
        width: 100%;
        height: 3;
        align: right middle;
    }
    #confirm-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, title: str, message: str):
        super().__init__()
        self.confirm_title = title
        self.confirm_msg = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Label(self.confirm_title, id="confirm-title")
            yield Label(self.confirm_msg, id="confirm-msg")
            with Horizontal(id="confirm-buttons"):
                yield Button("Cancel (Esc/n)", variant="default", id="btn-cancel")
                yield Button("Delete (y/Enter)", variant="error", id="btn-yes")

    def on_mount(self) -> None:
        self.query_one("#btn-cancel", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class PaneWidget(Vertical):
    """A single directory pane (Left or Right) in Commander mode with multi-selection support."""

    def __init__(self, pane_id: str, start_dir: Path, show_all: bool = True, **kwargs):
        super().__init__(id=pane_id, **kwargs)
        self.pane_id = pane_id
        self.current_dir = Path(start_dir).resolve()
        if not self.current_dir.is_dir():
            self.current_dir = self.current_dir.parent
        self.show_all = show_all
        self.items: List[Tuple[str, str, Path]] = []  # (label, type, path)
        self.selected_paths: Set[Path] = set()

    def compose(self) -> ComposeResult:
        with Horizontal(classes="pane-header"):
            yield Label(f"📂 {self.current_dir.name or '/'}", id=f"{self.pane_id}-title", classes="pane-title")
        yield OptionList(id=f"{self.pane_id}-list", classes="pane-file-list")
        with Horizontal(classes="pane-info-bar"):
            yield Label("", id=f"{self.pane_id}-info", classes="pane-info-label")

    def scan(self) -> None:
        """Scan directory items and clean up orphaned selections."""
        items: List[Tuple[str, str, Path]] = []
        excluded_dirs = {".git", ".venv", "node_modules", "__pycache__", "dist", "build"}
        supported_exts = (".md", ".markdown", ".html", ".htm", ".xhtml")

        # Parent directory
        if self.current_dir.parent != self.current_dir:
            items.append(("📁 /..", "parent_dir", self.current_dir.parent))

        try:
            subdirs = []
            files = []
            for entry in self.current_dir.iterdir():
                if not self.show_all and entry.name.startswith(".") and entry.name != "..":
                    continue
                if entry.is_dir():
                    if entry.name not in excluded_dirs or self.show_all:
                        subdirs.append(entry)
                elif entry.is_file():
                    if self.show_all:
                        files.append(entry)
                    else:
                        if entry.name.lower().endswith(supported_exts):
                            files.append(entry)

            for d in sorted(subdirs, key=lambda p: p.name.lower()):
                items.append((f"📁 {d.name}/", "dir", d))

            for f in sorted(files, key=lambda p: p.name.lower()):
                fname_lower = f.name.lower()
                if fname_lower.endswith((".html", ".htm", ".xhtml")):
                    icon = "🌐"
                elif fname_lower.endswith((".md", ".markdown")):
                    icon = "📄"
                elif fname_lower.endswith((".py", ".sh", ".bash", ".zsh", ".js", ".ts", ".json", ".toml", ".yaml", ".yml", ".c", ".cpp", ".rs", ".go")):
                    icon = "📜"
                else:
                    icon = "📝"
                
                try:
                    size_str = format_file_size(f.stat().st_size)
                except Exception:
                    size_str = ""
                
                items.append((f"{icon} {f.name:<30} {size_str:>8}", "file", f))

        except Exception as e:
            items.append((f"⚠️ {e}", "error", self.current_dir))

        self.items = items
        # Remove selections not in current dir
        valid_paths = {p for _, _, p in self.items}
        self.selected_paths = {p for p in self.selected_paths if p in valid_paths}

    def refresh_pane(self, target_filename: str | None = None) -> None:
        """Scan directory and refresh option list with selection indicators."""
        self.scan()
        try:
            title_label = self.query_one(f"#{self.pane_id}-title", Label)
            title_label.update(f"📂 {self.current_dir}")

            opt_list = self.query_one(f"#{self.pane_id}-list", OptionList)
            opt_list.clear_options()

            target_idx = 0
            for idx, (label, item_type, path) in enumerate(self.items):
                if path in self.selected_paths:
                    display_prompt = f"⭐ {label}"
                else:
                    display_prompt = f"  {label}"
                
                opt_list.add_option(Option(prompt=display_prompt, id=f"{item_type}:{path}"))
                if target_filename and path.name == target_filename:
                    target_idx = idx

            if opt_list.option_count > 0:
                opt_list.highlighted = target_idx
            
            self.update_info_bar()
        except Exception:
            pass

    def update_info_bar(self) -> None:
        """Update bottom summary of the pane including selected count."""
        try:
            info_label = self.query_one(f"#{self.pane_id}-info", Label)
            total_items = len([i for i in self.items if i[1] in ("dir", "file")])
            dirs_count = len([i for i in self.items if i[1] == "dir"])
            files_count = len([i for i in self.items if i[1] == "file"])
            sel_count = len(self.selected_paths)
            if sel_count > 0:
                info_label.update(f"{total_items} items ({dirs_count} dirs, {files_count} files) | [bold yellow]{sel_count} selected[/]")
            else:
                info_label.update(f"{total_items} items ({dirs_count} dirs, {files_count} files)")
        except Exception:
            pass

    def get_highlighted_item(self) -> Optional[Tuple[str, str, Path]]:
        """Get currently highlighted item in this pane."""
        opt_list = self.query_one(f"#{self.pane_id}-list", OptionList)
        if opt_list.highlighted is not None and 0 <= opt_list.highlighted < len(self.items):
            return self.items[opt_list.highlighted]
        return None

    def get_effective_targets(self) -> List[Path]:
        """Get selected paths if any; otherwise return currently highlighted file/dir."""
        if self.selected_paths:
            return sorted(list(self.selected_paths))
        item = self.get_highlighted_item()
        if item and item[1] in ("file", "dir"):
            return [item[2]]
        return []

    def toggle_select_highlighted(self) -> None:
        """Toggle selection of current highlighted item and advance cursor down."""
        opt_list = self.query_one(f"#{self.pane_id}-list", OptionList)
        item = self.get_highlighted_item()
        if not item or item[1] not in ("file", "dir"):
            return

        path = item[2]
        if path in self.selected_paths:
            self.selected_paths.remove(path)
        else:
            self.selected_paths.add(path)

        # Update prompt in OptionList
        cur_idx = opt_list.highlighted
        if cur_idx is not None:
            label, item_type, _ = item
            new_prompt = f"⭐ {label}" if path in self.selected_paths else f"  {label}"
            # Recreate option
            opt_list.replace_option_prompt_at_index(cur_idx, new_prompt)
            # Advance cursor down like classic MC
            if cur_idx + 1 < len(self.items):
                opt_list.highlighted = cur_idx + 1
        
        self.update_info_bar()

    def select_all_items(self) -> None:
        """Select all files and directories in this pane."""
        for _, item_type, path in self.items:
            if item_type in ("file", "dir"):
                self.selected_paths.add(path)
        self.refresh_pane()

    def unselect_all_items(self) -> None:
        """Unselect all items in this pane."""
        self.selected_paths.clear()
        self.refresh_pane()


class CommanderScreen(ModalScreen[Optional[Path]]):
    """Full-screen Midnight Commander-style dual pane file manager with Phase 3 batch operations."""

    BINDINGS = [
        Binding("tab", "switch_pane", "Switch Pane", priority=True),
        Binding("insert", "toggle_select", "Select (Ins/Space)", priority=True),
        Binding("space", "toggle_select", "Select", show=False, priority=True),
        Binding("f3", "view_file", "View", priority=True),
        Binding("f4", "edit_file", "Edit", priority=True),
        Binding("f5", "copy_file", "Copy", priority=True),
        Binding("f6", "move_file", "Ren/Mov", priority=True),
        Binding("f7", "mkdir_folder", "Mkdir", priority=True),
        Binding("f8", "delete_file", "Del", priority=True),
        Binding("ctrl+a", "toggle_all", "Hidden", priority=True),
        Binding("ctrl+o", "toggle_mode", "Reader", priority=True),
        Binding("f10", "quit_app", "Quit", priority=True),
        Binding("escape", "toggle_mode", "Back/Reader", priority=True, show=False),
        Binding("q", "toggle_mode", "Back/Reader", show=False),
        Binding("r", "refresh_both", "Reload", show=False),
    ]

    CSS = """
    CommanderScreen {
        background: $surface;
        layout: vertical;
    }

    #commander-main {
        width: 100%;
        height: 1fr;
        layout: horizontal;
    }

    PaneWidget {
        width: 1fr;
        height: 100%;
        border: solid $panel;
        background: $surface;
        padding: 0;
    }

    PaneWidget.-active {
        border: thick $primary;
        background: $boost;
    }

    .pane-header {
        height: 1;
        background: $primary-darken-2;
        padding: 0 1;
    }

    .pane-title {
        text-style: bold;
        color: $accent;
        width: 100%;
    }

    .pane-file-list {
        height: 1fr;
        background: $panel;
        border: none;
    }

    .pane-info-bar {
        height: 1;
        background: $footer-background;
        padding: 0 1;
    }

    .pane-info-label {
        color: $text-muted;
        text-style: italic;
    }

    #commander-footer {
        height: 1;
        background: $footer-background;
        dock: bottom;
    }
    """

    def __init__(
        self,
        current_path: Path | None = None,
        show_all: bool | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        # Load remembered paths
        saved_left = get_config_value("commander_left_dir")
        if saved_left and Path(saved_left).is_dir():
            start_left = Path(saved_left).resolve()
        else:
            start_left = current_path.parent if current_path and current_path.exists() else Path.cwd()

        saved_right = get_config_value("commander_right_dir")
        if saved_right and Path(saved_right).is_dir():
            start_right = Path(saved_right).resolve()
        else:
            start_right = Path.home() if Path.home().is_dir() else Path.cwd()
        
        self.start_left = start_left
        self.start_right = start_right
        
        if show_all is None:
            self.show_all = bool(get_config_value("show_all_files", True))
        else:
            self.show_all = show_all

        self.active_pane_id = "left-pane"

    def compose(self) -> ComposeResult:
        with Horizontal(id="commander-main"):
            yield PaneWidget("left-pane", start_dir=self.start_left, show_all=self.show_all)
            yield PaneWidget("right-pane", start_dir=self.start_right, show_all=self.show_all)
        yield Footer(id="commander-footer")

    def on_mount(self) -> None:
        left_pane = self.query_one("#left-pane", PaneWidget)
        right_pane = self.query_one("#right-pane", PaneWidget)
        left_pane.refresh_pane()
        right_pane.refresh_pane()
        self._update_active_pane_style()

    def _update_active_pane_style(self) -> None:
        try:
            left_pane = self.query_one("#left-pane", PaneWidget)
            right_pane = self.query_one("#right-pane", PaneWidget)
        except Exception:
            return

        if self.active_pane_id == "left-pane":
            left_pane.add_class("-active")
            right_pane.remove_class("-active")
            try:
                left_pane.query_one("#left-pane-list", OptionList).focus()
            except Exception:
                pass
        else:
            right_pane.add_class("-active")
            left_pane.remove_class("-active")
            try:
                right_pane.query_one("#right-pane-list", OptionList).focus()
            except Exception:
                pass

    def on_key(self, event: events.Key) -> None:
        """Handle key events explicitly to prevent bubbling to parent App bindings."""
        if event.key == "tab":
            event.stop()
            event.prevent_default()
            self.action_switch_pane()
        elif event.key in ("insert", "space"):
            event.stop()
            event.prevent_default()
            self.action_toggle_select()

    def action_switch_pane(self) -> None:
        """Switch active pane between Left and Right (Tab)."""
        self.active_pane_id = "right-pane" if self.active_pane_id == "left-pane" else "left-pane"
        self._update_active_pane_style()

    def action_toggle_select(self) -> None:
        """Toggle select on highlighted item (Insert / Space)."""
        active_pane = self.query_one(f"#{self.active_pane_id}", PaneWidget)
        active_pane.toggle_select_highlighted()

    def action_toggle_all(self) -> None:
        """Toggle showing hidden files."""
        self.show_all = not self.show_all
        set_config_value("show_all_files", self.show_all)
        left_pane = self.query_one("#left-pane", PaneWidget)
        right_pane = self.query_one("#right-pane", PaneWidget)
        left_pane.show_all = self.show_all
        right_pane.show_all = self.show_all
        left_pane.refresh_pane()
        right_pane.refresh_pane()
        self.notify(f"Hidden files: {'Shown' if self.show_all else 'Hidden'}", timeout=1.5)

    def action_refresh_both(self) -> None:
        """Reload both panes."""
        left_pane = self.query_one("#left-pane", PaneWidget)
        right_pane = self.query_one("#right-pane", PaneWidget)
        left_pane.refresh_pane()
        right_pane.refresh_pane()
        self.notify("Directories reloaded", timeout=1.0)

    def action_toggle_mode(self) -> None:
        """Return to Reader Mode."""
        self._save_dirs()
        self.dismiss(None)

    def action_quit_app(self) -> None:
        """Quit the application entirely (F10)."""
        self._save_dirs()
        self.app.exit()

    def action_view_file(self) -> None:
        """View highlighted file in Reader Mode (F3 / Enter)."""
        active_pane = self.query_one(f"#{self.active_pane_id}", PaneWidget)
        item = active_pane.get_highlighted_item()
        if not item:
            return
        
        label, item_type, path = item
        if item_type == "file":
            self._save_dirs()
            self.dismiss(path)
        elif item_type in ("parent_dir", "dir"):
            old_name = active_pane.current_dir.name
            active_pane.current_dir = path.resolve()
            active_pane.selected_paths.clear()
            active_pane.refresh_pane(target_filename=old_name if item_type == "parent_dir" else None)
            self._save_dirs()

    def action_edit_file(self) -> None:
        """Open highlighted file in editor (F4)."""
        active_pane = self.query_one(f"#{self.active_pane_id}", PaneWidget)
        item = active_pane.get_highlighted_item()
        if not item or item[1] != "file":
            self.notify("Please select a file to edit", title="Edit", severity="warning")
            return
        
        file_path = item[2]
        editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "vim"
        editor_path = shutil.which(editor) or shutil.which("vim") or shutil.which("vi") or shutil.which("nano")
        if not editor_path:
            self.notify(f"Editor '{editor}' not found in PATH", title="Error", severity="error")
            return

        try:
            with self.app.suspend():
                import subprocess
                subprocess.run([editor_path, str(file_path.resolve())])
            active_pane.refresh_pane(target_filename=file_path.name)
            self.notify(f"Edited: {file_path.name}", timeout=1.5)
        except Exception as e:
            self.notify(f"Error opening editor: {e}", title="Error", severity="error")

    # ==================== Phase 2 & 3: Batch File Operations (F5, F6, F7, F8) ====================

    def _get_other_pane(self) -> PaneWidget:
        other_id = "right-pane" if self.active_pane_id == "left-pane" else "left-pane"
        return self.query_one(f"#{other_id}", PaneWidget)

    def action_copy_file(self) -> None:
        """Copy selected file(s) or directory to target (F5)."""
        active_pane = self.query_one(f"#{self.active_pane_id}", PaneWidget)
        other_pane = self._get_other_pane()
        targets = active_pane.get_effective_targets()
        if not targets:
            self.notify("Please select file(s) or folder(s) to copy", severity="warning")
            return

        if len(targets) == 1:
            src_path = targets[0]
            dest_default = str(other_pane.current_dir / src_path.name)
            title = f"Copy '{src_path.name}' to:"
        else:
            dest_default = str(other_pane.current_dir)
            title = f"Copy {len(targets)} selected items to directory:"

        prompt = PromptModal(
            title=title,
            initial_value=dest_default,
            placeholder="Destination path...",
        )

        def _do_copy(dest_str: str | None) -> None:
            if not dest_str:
                return
            dest = Path(dest_str).expanduser().resolve()
            try:
                copied_count = 0
                for target in targets:
                    if len(targets) == 1 and not dest.is_dir() and not dest.exists():
                        target_dest = dest
                    else:
                        target_dest = dest / target.name if dest.is_dir() else dest
                    
                    if target.is_dir():
                        shutil.copytree(target, target_dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(target, target_dest)
                    copied_count += 1

                active_pane.selected_paths.clear()
                self.action_refresh_both()
                self.notify(f"Successfully copied {copied_count} item(s)", title="F5 Copy", timeout=2)
            except Exception as e:
                self.notify(f"Copy failed: {e}", title="Error", severity="error", timeout=3)

        self.app.push_screen(prompt, _do_copy)

    def action_move_file(self) -> None:
        """Rename or move selected file(s)/directory (F6)."""
        active_pane = self.query_one(f"#{self.active_pane_id}", PaneWidget)
        other_pane = self._get_other_pane()
        targets = active_pane.get_effective_targets()
        if not targets:
            self.notify("Please select file(s) or folder(s) to move/rename", severity="warning")
            return

        if len(targets) == 1:
            src_path = targets[0]
            dest_default = str(other_pane.current_dir / src_path.name)
            title = f"Rename / Move '{src_path.name}' to:"
        else:
            dest_default = str(other_pane.current_dir)
            title = f"Move {len(targets)} selected items to directory:"

        prompt = PromptModal(
            title=title,
            initial_value=dest_default,
            placeholder="Target path...",
        )

        def _do_move(dest_str: str | None) -> None:
            if not dest_str:
                return
            dest = Path(dest_str).expanduser().resolve()
            try:
                moved_count = 0
                for target in targets:
                    if len(targets) == 1 and not dest.is_dir():
                        target_dest = dest
                    else:
                        target_dest = dest / target.name if dest.is_dir() else dest
                    shutil.move(str(target), str(target_dest))
                    moved_count += 1

                active_pane.selected_paths.clear()
                self.action_refresh_both()
                self.notify(f"Successfully moved {moved_count} item(s)", title="F6 Move", timeout=2)
            except Exception as e:
                self.notify(f"Move failed: {e}", title="Error", severity="error", timeout=3)

        self.app.push_screen(prompt, _do_move)

    def action_mkdir_folder(self) -> None:
        """Create new directory in active pane (F7)."""
        active_pane = self.query_one(f"#{self.active_pane_id}", PaneWidget)
        prompt = PromptModal(
            title=f"Create new directory in {active_pane.current_dir.name}:",
            placeholder="New directory name...",
        )

        def _do_mkdir(dir_name: str | None) -> None:
            if not dir_name:
                return
            new_dir = active_pane.current_dir / dir_name
            try:
                new_dir.mkdir(parents=True, exist_ok=False)
                active_pane.refresh_pane(target_filename=new_dir.name)
                self._save_dirs()
                self.notify(f"Created directory: {dir_name}", title="F7 Mkdir", timeout=2)
            except Exception as e:
                self.notify(f"Mkdir failed: {e}", title="Error", severity="error", timeout=3)

        self.app.push_screen(prompt, _do_mkdir)

    def action_delete_file(self) -> None:
        """Delete selected file(s) or directory (F8)."""
        active_pane = self.query_one(f"#{self.active_pane_id}", PaneWidget)
        targets = active_pane.get_effective_targets()
        if not targets:
            self.notify("Please select file(s) or folder(s) to delete", severity="warning")
            return

        if len(targets) == 1:
            target = targets[0]
            item_type_label = "Directory (and contents)" if target.is_dir() else "File"
            msg = f"Permanently delete {item_type_label}:\n{target.name} ?"
        else:
            msg = f"Permanently delete {len(targets)} selected items ?"

        confirm_modal = ConfirmModal(
            title="⚠️ Delete Confirmation",
            message=msg,
        )

        def _do_delete(confirmed: bool | None) -> None:
            if not confirmed:
                return
            try:
                deleted_count = 0
                for target in targets:
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                    deleted_count += 1

                active_pane.selected_paths.clear()
                self.action_refresh_both()
                self.notify(f"Successfully deleted {deleted_count} item(s)", title="F8 Delete", timeout=2)
            except Exception as e:
                self.notify(f"Delete failed: {e}", title="Error", severity="error", timeout=3)

        self.app.push_screen(confirm_modal, _do_delete)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle Enter key or double click on file list."""
        event.stop()
        if event.option_list.id == "left-pane-list":
            self.active_pane_id = "left-pane"
        elif event.option_list.id == "right-pane-list":
            self.active_pane_id = "right-pane"
        self._update_active_pane_style()
        self.action_view_file()

    def _save_dirs(self) -> None:
        """Save directory state in config."""
        try:
            left_pane = self.query_one("#left-pane", PaneWidget)
            right_pane = self.query_one("#right-pane", PaneWidget)
            set_config_value("commander_left_dir", str(left_pane.current_dir))
            set_config_value("commander_right_dir", str(right_pane.current_dir))
        except Exception:
            pass
