"""Help modal dialog listing all keyboard shortcuts and features in mdreader."""
from __future__ import annotations
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Label, Button
from textual.binding import Binding
from mdreader.utils.config import get_keybindings, format_keybinding_display


def get_help_sections() -> list[tuple[str, list[tuple[str, str]]]]:
    """Dynamically build help sections from active keybindings."""
    bindings = get_keybindings()

    def k(action: str, fallback: str = "") -> str:
        keys = bindings.get(action, [])
        if keys:
            return format_keybinding_display(keys)
        return fallback

    return [
        (
            "📖 核心閱讀與翻頁導航 (Navigation)",
            [
                (k("page_up", "PageUp / u"), "整頁向上翻頁 (Page Up)"),
                (k("page_down", "PageDown / i"), "整頁向下翻頁 (Page Down)"),
                (f"{k('scroll_up', '↑ / j')} / {k('scroll_down', '↓ / k')}", "逐行向上 / 向下垂直平滑捲動"),
                (f"{k('scroll_left', '← / d')} / {k('scroll_right', '→ / f')}", "向左 / 向右水平捲動 (關閉折行時使用)"),
                ("gg / Home", "快速回到文件最上方 (Jump to Top)"),
                (f"{k('scroll_end', 'G')} / End", "快速跳至文件最下方 (Jump to Bottom)"),
                (f"{k('open_goto_line', ':')}123 / 123G / 50gg", "跳轉至指定行號 (Goto Line Number)"),
            ],
        ),
        (
            "📑 檢視、排版與大綱 (View & Outline)",
            [
                (k("toggle_toc", "Ctrl+O"), "章節大綱目錄 (TOC Outline，按 Enter 即時跳轉)"),
                (k("toggle_wrap", "w"), "切換自動折行 (Toggle Soft Line Wrap)"),
                (k("toggle_line_numbers", "l"), "切換行號欄顯示 (Toggle Line Numbers, 程式碼/純文字)"),
                (k("toggle_theme", "t"), "切換色彩主題 (Cycle Theme, 10+ 款主題持久化記憶)"),
                (f"{k('zoom_out', '-')} / {k('zoom_in', '= / +')}", "縮放閱讀版面寬度 (Adjust Reading Width)"),
            ],
        ),
        (
            "🔍 搜尋、書籤與超連結 (Search & Bookmarks)",
            [
                (f"{k('open_search', '/')} [query] Enter", "文件內全文搜尋 (In-document Search)"),
                (f"{k('search_next', 'n')} / {k('search_prev', 'N')}", "跳至下一處 / 上一處搜尋結果 (Next / Prev Match)"),
                (k("open_link", "gx"), "擷取文件超連結並於預設瀏覽器開啟 (Open Hyperlink)"),
                ("M + [a-z]", "在當前行設定書籤 (Set Mark, Shift+M)"),
                ("' + [a-z]", "跳轉至指定書籤行號 (Jump to Mark)"),
                (k("list_marks", "Ctrl+M"), "書籤總覽清單視窗 (List All Marks)"),
            ],
        ),
        (
            "📁 檔案總管與檢索 (File Discovery)",
            [
                (k("open_file_picker", "o"), "檔案選擇器 (File Picker, Ctrl+R 最近檔案, Ctrl+H 隱藏檔)"),
                (k("open_commander", "O"), "Midnight Commander 雙欄檔案總管 (MC Mode)"),
                ("Ctrl+D", "目錄書籤與快速路徑跳轉 (~, CWD, Downloads, Desktop)"),
                ("Ctrl+F", "資料夾全文關鍵字檢索 (Ripgrep Accelerated Search)"),
            ],
        ),
        (
            "🛠️ 編輯、匯出與外部整合 (Integration)",
            [
                (k("edit_in_editor", "v / F4"), "開啟外部編輯器 ($EDITOR / vim) 編輯並即時熱重載"),
                (k("export_document", "e"), "匯出文件 (獨立 Styled HTML / 純文字 / Markdown)"),
                (k("copy_code_block", "Y / Ctrl+K"), "提取並複製程式碼區塊 (Copy Code Block)"),
                (k("copy_selected_text", "y / c / Ctrl+C"), "複製選取文字或全文至剪貼簿 (Copy to Clipboard)"),
                (k("toggle_mouse_mode", "m"), "切換滑鼠模式 (Toggle Mouse / Terminal Selection)"),
                (k("open_in_terminal", "Ctrl+T"), "在當前檔案目錄開啟終端機 Shell"),
                (k("toggle_cmd_prompt", "T"), "切換終端命令提示列 (Toggle Terminal Prompt Bar)"),
                (k("reveal_in_finder", "Ctrl+Shift+O"), "在系統檔案管理員中定位 (Finder / xdg-open)"),
                (k("reload_file", "r"), "手動重新載入檔案內容 (Reload File)"),
                (k("open_help", "h / ? / F1"), "開啟本說明視窗 (Help)"),
                (f"{k('quit', 'q')} / {k('handle_escape', 'Esc')}", "離開 mdreader 閱讀器 / 關閉浮動視窗"),
            ],
        ),
        (
            "🖼️ 圖片檢視與縮放 (Image Viewing & Zoom)",
            [
                (k("zoom_in", "+ / = / z"), "放大圖片縮放比例 (+20% Zoom In)"),
                (k("zoom_out", "- / Z"), "縮小圖片縮放比例 (-20% Zoom Out)"),
                (k("reset_zoom", "0"), "重設圖片縮放比例為 100% (Reset Zoom)"),
                ("↑ / ↓ / ← / → / jkdf", "平移移動檢視大圖 (Pan Image)"),
                (f"{k('edit_in_editor', 'v / F4')} / Enter", "呼叫系統預設看圖程式開啟原圖 (System Viewer)"),
            ],
        ),
    ]


HELP_SECTIONS = get_help_sections()


class ReaderHelpModal(ModalScreen[None]):
    """Modal screen displaying all shortcuts and functions in mdreader."""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Close", priority=True),
        Binding("q", "dismiss_modal", "Close", priority=True),
        Binding("h", "dismiss_modal", "Close", priority=True),
        Binding("enter", "dismiss_modal", "Close", priority=True),
    ]

    CSS = """
    ReaderHelpModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.8);
    }
    #help-container {
        width: 88;
        height: 85%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    #help-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 1;
    }
    #help-scroll {
        height: 1fr;
        background: $panel;
        padding: 0 1;
        border: solid $panel-darken-1;
        margin-bottom: 1;
    }
    .help-section-title {
        text-style: bold;
        color: $warning;
        margin-top: 1;
        margin-bottom: 0;
    }
    .help-row {
        height: auto;
        padding: 0 1;
    }
    .help-key {
        width: 26;
        text-style: bold;
        color: $secondary;
    }
    .help-desc {
        width: 1fr;
        color: $text;
    }
    #help-close-bar {
        height: 3;
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="help-container"):
            yield Label("💡 mdreader 完整快速鍵與功能指南 (Help)", id="help-title")
            with VerticalScroll(id="help-scroll"):
                for sec_title, items in get_help_sections():
                    yield Label(sec_title, classes="help-section-title")
                    for key, desc in items:
                        with Horizontal(classes="help-row"):
                            yield Label(key, classes="help-key")
                            yield Label(desc, classes="help-desc")
            with Horizontal(id="help-close-bar"):
                yield Button("關閉說明 (Esc / q / Enter)", variant="primary", id="close-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-btn":
            self.dismiss(None)

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)
