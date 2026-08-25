# mdreader — Terminal Markdown Reader

An interactive terminal Markdown previewer with native **Mermaid flowchart rendering** support (GUI-like experience in CLI), inspired by [leaf](https://github.com/RivoLink/leaf).

## ✨ 功能特色

- 📑 **豐富的 Markdown 與 Mermaid 流程圖渲染**：標題、表格、列表、引用區塊、語法高亮程式碼區塊，以及原生的 ```` ```mermaid ```` ASCII/Unicode 流程圖繪製。
- ⚡ **GB 級超大檔案極限讀取架構**：內建 Zero-copy `mmap` 記憶體映射與二進位行索引，10 萬行超大檔案 30ms 極速載入，RAM 佔用低於 10MB，並具備次毫秒級二進位搜尋。
- 💻 **Vim 風格導航與行號跳轉**：
  - 自動折行切換（`w` / `Alt+Z`）
  - 快速跳轉行號（`:123`、`500G`、`42gg`）
  - Vim 書籤功能（`m` + 按鍵建立書籤、`'` + 按鍵跳轉、`Ctrl+M` 開啟書籤清單）
  - 快速擷取超連結並以預設瀏覽器開啟（`gx`）
- 📊 **響應式增強型狀態列**：
  - 即時顯示：`1.5M │ Markdown │ [WRAP] │ Ln 42/1000 (4%)`
  - 螢幕寬度較窄時（< 95 欄）自動隱藏時鐘等輔助資訊，保持介面簡潔。
- 📁 **Midnight Commander 雙欄檔案管理模式 (`Ctrl+O`)**：
  - `Tab` 切換面板、`Insert`/`Space` 批次多選、`F3` 檢視、`F4` 編輯、`F5` 複製、`F6` 移動/重命名、`F7` 建立目錄、`F8` 刪除、`s`/`F2` 檔案排序（名稱/大小/時間/副檔名）、`Ctrl+D` 目錄書籤、`Ctrl+F` 全文搜尋。
- 🔍 **資料夾全文檢索 (`Ctrl+F`)**：
  - 支援 `ripgrep (rg)` 引擎加速與 Python 原生串流搜尋，在檔案樹中搜尋包含關鍵字的檔案並直接跳轉至對應行號。
- 🔖 **目錄書籤與快速路徑跳轉 (`Ctrl+D`)**：
  - 快速跳轉至家目錄 (`~`)、工作區目錄、Downloads、Desktop、Documents、根目錄 (`/`) 與最近開啟目錄。
- 📂 **Fzf 風格模糊檔案選擇器 (`o`)**：
  - 子序列模糊評分演算法、最近檔案快速切換（`Ctrl+R`）、隱藏檔切換（`Ctrl+H` / `Ctrl+A`）。
- 📤 **獨立 HTML / 純文字匯出 (`e` / 命令列 `--export-html`)**：
  - 一鍵將文件匯出為具備現代深色/淺色排版 CSS 的獨立 HTML 檔或純文字檔。
- 💻 **程式碼區塊快速提取與複製 (`Y` / `Ctrl+K`)**：
  - 自動列出文件內所有程式碼區塊，點選即可一鍵複製至系統剪貼簿。
- 🛠️ **外部工具與終端機整合**：
  - `v` / `F4`：叫用 `$EDITOR` / `vim` 編輯文件並自動熱重載
  - `Ctrl+T`：在當前檔案目錄開啟終端機 Shell
  - `Ctrl+Shift+O`：在系統檔案管理員（Finder / xdg-open）中顯示該檔案
- 🔄 **Watch 監聽模式**：偵測檔案變更自動重新載入（`-w` / `--watch`）。
- 🎨 **多款配色主題**：內建 10+ 款主題（`t` 循環切換、`--list-themes`），設定自動持久化保存。
- 🖱️ **滑鼠選取與剪貼簿同步**：支援 macOS `pbcopy`、Linux `wl-copy` / `xclip` 與 OSC 52。按 `m` 鍵切換滑鼠模式。
- 📟 **命令列自動化**：支援指定啟動行號（`+50` / `-l 50`）、無介面直接匯出（`--export-html`）與管線輸出（`--inline`）。

---

## 🚀 安裝方式

```bash
# 推薦使用 pipx 安裝（自動加入環境變數且獨立隔離）
git clone https://github.com/candyz/mdreader.git
cd mdreader
pipx install .
mdreader --version
```

---

## 🎯 使用範例

```bash
# 1. 直接開啟檔案選擇器
mdreader

# 2. 開啟檔案並直接跳轉至第 50 行
mdreader +50 README.md
mdreader -l 50 README.md

# 3. 預覽 HTML 網頁或巨量 Log 資料檔
mdreader index.html
mdreader gigantic_data.log

# 4. 監聽模式：檔案變更時自動重載
mdreader -w README.md

# 5. 列出所有主題並於啟動時指定主題
mdreader --list-themes
mdreader -t tokyo-night README.md

# 6. 無介面直接將 Markdown 匯出為 HTML 或純文字
mdreader README.md --export-html output.html
mdreader README.md --export-txt output.txt

# 7. 終端標準輸出預覽（適合搭配 fzf 預覽視窗）
mdreader --inline README.md

# 8. 由管線讀取內容
cat test.md | mdreader
curl -s https://example.com | mdreader

# 9. 指定特定語法突顯（例如 sh, python, json 等，純文字預設為 sh）
mdreader -s python snippet.dat
mdreader -s sh config.env
```

---

## ⌨️ 快捷鍵一覽 (TUI 閱讀模式)

| 按鍵 | 動作說明 |
| :--- | :--- |
| `q` / `Esc` | 離開程式 / 關閉彈出視窗或搜尋列 |
| `h` / `?` / `F1` | **快速鍵說明視窗 (Help)**：列出所有快速鍵功能指南 |
| `o` | **開啟檔案選擇器**：瀏覽檔案、`Ctrl+R` 最近檔案、`Ctrl+D` 目錄書籤、`Ctrl+F` 全文搜尋 |
| `Ctrl+O` | **章節大綱目錄 (TOC)**：瀏覽文件標題大綱，按 Enter 即時跳轉 |
| `O` | **Midnight Commander 雙欄檔案總管**：`Tab` 切換雙欄、`Ins`/`Space` 多選、`F3` 檢視、`F4` 編輯、`F5` 複製、`F6` 移動、`F7` 建立目錄、`F8` 刪除、`s` 排序、`Ctrl+D` 書籤、`Ctrl+F` 全文搜尋 |
| `w` | **切換自動折行**：在自動換行與水平捲動模式之間切換 |
| `l` | **切換行號顯示**：在原始碼與純文字檔案中顯示/隱藏左側行號欄 |
| `gx` | **擷取並開啟超連結**：擷取文件中的超連結並於預設瀏覽器中開啟 |
| `m` + `[a-z]` | **設定書籤**：在當前行建立指定代號的書籤 |
| `'` + `[a-z]` | **跳轉書籤**：跳轉至先前建立的指定書籤行 |
| `Ctrl+M` | **書籤清單**：開啟視窗檢視並選擇已儲存的書籤 |
| `:` / `[N]G` / `[N]gg` | **跳轉行號**：直接跳轉至指定行號 |
| `e` | **匯出文件**：將文件匯出為獨立 HTML、純文字或 Markdown |
| `Y` / `Ctrl+K` | **複製程式碼區塊**：快速提取並複製程式碼區塊至剪貼簿 |
| `v` | **外部編輯器編輯**：以 Vim 或 `$EDITOR` 開啟編輯並熱重載 |
| `Ctrl+T` | **開啟終端機 Shell**：在當前檔案目錄開啟互動式終端機 |
| `T` | **切換終端命令提示列**：在狀態列上方顯示 Midnight Commander 風格之 Shell Prompt 輸入列 |
| `Ctrl+Shift+O` | **檔案管理員中顯示**：在系統檔案管理員（Finder / xdg-open）中開啟所在位置 |
| `t` | **切換色彩主題**：循環切換內建配色主題 (包含全新 `vim-dark`、`github-dark`、`monokai` 等) |
| `/` | **文件搜尋**：Vim 風格關鍵字搜尋（`n` 下一處、`N` 上一處） |
| `Page Up` / `u` | 上一頁 |
| `Page Down` / `i` | 下一頁 |
| `↑` / `j` | 向上捲動一行 |
| `↓` / `k` | 向下捲動一行 |
| `gg` / `Home` | 回到文件最上方 |
| `G` / `End` | 跳至文件最下方 |
| `m` | **切換滑鼠攔截模式**：關閉時完全恢復終端原生滑鼠框選操作 |
| `-` / `=` / `+` | 調整閱讀版面寬度 |
| `=` / `+` | **放大圖片**：提升圖片縮放比例 (+20% Zoom In) |
| `-` | **縮小圖片**：降低圖片縮放比例 (-20% Zoom Out) |
| `0` | **重設圖片縮放**：將圖片縮放比例重設為 100% (Reset Zoom) |
| `↑` / `↓` / `←` / `→` / `jkdf` | **平移檢視大圖**：在視窗中平移移動圖片 (Pan Image) |

---

## ⚙️ 自訂鍵盤快速鍵 (`~/.config/mdreader/config.json`)

您可以在 `~/.config/mdreader/config.json` 中加入 `"keybindings"` 區塊自訂任何快速鍵。每個動作可綁定單一字串或多個按鍵別名陣列：

```json
{
  "theme": "vim-dark",
  "keybindings": {
    "quit": ["q", "escape"],
    "open_file_picker": "o",
    "toggle_toc": "ctrl+o",
    "open_commander": "O",
    "toggle_wrap": "w",
    "edit_in_editor": ["v", "f4"],
    "toggle_theme": "t",
    "open_help": ["h", "?", "f1"],
    "open_search": "/",
    "open_goto_line": ":",
    "page_down": ["pagedown", "i"],
    "page_up": ["pageup", "u"],
    "scroll_down": ["down", "k"],
    "scroll_up": ["up", "j"],
    "zoom_in": ["=", "+"],
    "zoom_out": "-",
    "toggle_line_numbers": "l",
    "reset_zoom": "0"
  }
}
```

### 支援之 Action 動作名稱一覽表

| Action 動作名稱 | 預設快捷鍵 | 功能說明 |
| :--- | :--- | :--- |
| `quit` | `q` | 離開閱讀器 |
| `open_file_picker` | `o` | 開啟模糊搜尋檔案選擇器 |
| `toggle_toc` | `ctrl+o` | 開啟章節大綱目錄 (TOC) |
| `open_commander` | `O` | 開啟 Midnight Commander 雙欄檔案總管 |
| `toggle_wrap` | `w` | 切換自動折行 |
| `edit_in_editor` | `v`, `f4` | 呼叫外部編輯器 / 看圖軟體 |
| `toggle_theme` | `t` | 切換色彩主題 |
| `open_help` | `h`, `?`, `f1` | 開啟說明視窗 |
| `handle_escape` | `escape` | 取消 / 關閉浮動視窗 |
| `open_search` | `/` | 文件內全文搜尋 |
| `open_goto_line` | `:` | 跳轉至指定行號 |
| `search_next` | `n` | 跳至下一處搜尋結果 |
| `search_prev` | `N` | 跳至上一處搜尋結果 |
| `page_up` | `pageup`, `u` | 整頁向上翻頁 |
| `page_down` | `pagedown`, `i` | 整頁向下翻頁 |
| `scroll_up` | `up`, `j` | 向上捲動 |
| `scroll_down` | `down`, `k` | 向下捲動 |
| `scroll_left` | `left`, `d` | 向左水平捲動 (看圖或關閉折行時) |
| `scroll_right` | `right`, `f` | 向右水平捲動 |
| `scroll_end` | `G` | 跳至文件最底部 |
| `zoom_in` | `=`, `+` | 放大閱讀版面 / 圖片 |
| `zoom_out` | `-` | 縮小閱讀版面 / 圖片 |
| `reset_zoom` | `0` | 重設縮放比例為 100% |
| `export_document` | `e` | 匯出文件 (HTML/Text/Markdown) |
| `copy_code_block` | `Y`, `ctrl+k` | 複製程式碼區塊 |
| `copy_selected_text`| `y`, `c`, `ctrl+c`, `ctrl+y` | 複製選取文字或全文 |
| `toggle_mouse_mode` | `m` | 切換滑鼠選取模式 |
| `toggle_cmd_prompt` | `T` | 切換終端命令提示列 |
| `open_in_terminal` | `ctrl+t` | 開啟終端機 Shell |
| `reveal_in_finder` | `ctrl+shift+o` | 系統檔案管理員中定位 |
| `toggle_line_numbers`| `l` | 切換行號欄顯示 |
| `reload_file` | `r` | 手動重新載入檔案 |

---

## 📚 相關文件
- [使用者手冊 (繁體中文)](docs/user_manual_zh-TW.md) | [User Manual (English)](docs/user_manual.md)
- [部署安裝指南 (繁體中文)](docs/deployment_guide_zh-TW.md) | [Deployment Guide (English)](docs/deployment_guide.md)
- [實作規劃書 (繁體中文)](docs/implementation_plan_zh-TW.md) | [Implementation Plan (English)](docs/implementation_plan.md)

---

## 📄 開源授權 (License)

本專案採用 [MIT License](LICENSE) 授權開源。
