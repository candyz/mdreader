# mdreader — Terminal Markdown Reader

An interactive terminal Markdown previewer with native **Mermaid flowchart rendering** support (GUI-like experience in CLI), inspired by [leaf](https://github.com/RivoLink/leaf).

## Features

- 📑 **豐富的 Markdown 渲染**：標題、表格、列表、引用區塊，以及具備語法高亮的代碼區塊。
- 💻 **Vim 風格程式源碼與點檔案檢視**：支援各種程式語言（`.c`, `.h`, `.js`, `.css`, `.sh`, `.py`, `.rs`, `.go`, `Makefile` 等）及設定檔（`.vimrc`, `.bashrc` 等）的語法高亮排版檢視。
- 🌐 **原生 HTML 文件支援**：零外部依賴直接渲染 `.html` / `.htm` 網頁檔與管線輸入之 HTML，完整保留表格、標題、代碼與列表。
- 📊 **Mermaid 流程圖支援**：自動將 ```` ```mermaid ```` 圖表轉換為 ASCII/Unicode 文字圖表內嵌顯示，完全解決傳統工具因 mermaid 語法而崩潰的問題。
- 📁 **Midnight Commander 雙欄檔案管理模式 (`Ctrl+O`)**：左右雙欄瀏覽、`Tab` 切換、`Ins`/`Space` 批次多選、`F3` 檢視、`F4` 編輯、`F5` 複製、`F6` 移動/重命名、`F7` 新增資料夾、`F8` 刪除、`?` 快捷鍵說明與雙欄目錄獨立記憶。
- 📑 **互動式大綱目錄 (TOC Outline)**：自動解析文件標題並提供可搜尋跳轉的大綱視窗（按 `O` 開啟）。
- 📂 **檔案選擇器 (File Picker)**：快速選擇檔案並支援 `Ctrl+A` 顯示隱藏檔案與路徑記憶（按 `o` 開啟或直接執行 `mdreader`）。
- 🔄 **Watch 監聽模式**：偵測檔案變更自動重新載入（`-w` / `--watch`）。
- 🎨 **多款配色主題與記憶**：內建 10+ 款深色/淺色主題（按 `t` 循環切換），設定自動持久化保存至 `~/.config/mdreader/config.json`。
- 🔍 **文件內搜尋欄**：Vim 風格搜尋列（按 `/` 開啟），支援 `n` / `N` 快速跳轉匹配處。
- 📝 **外部編輯器整合**：按 `v` 隨時叫用 `$EDITOR` 或 `vim` 編輯文件，存檔離開後即時重載。
- 🖱️ **滑鼠選取與剪貼簿同步**：支援 macOS `pbcopy`、Linux `xclip` / `wl-copy` 與 Textual OSC 52。
- 🖲️ **滑鼠模式切換**：按 `m` 鍵可快速在 TUI 互動模式與終端原生滑鼠框選模式之間切換。
- ⚡ **互動式 TUI**：全螢幕極大化閱讀介面、平滑垂直與水平左右捲動（`d` / `f` / `←` / `→`）、欄寬縮放（`-` / `=`）、Vim 導航鍵（`j`/`k`/`gg`/`G`/`q`/`Esc`）。
- 📟 **Inline 模式**：透過 `--inline` 直接以 ANSI 彩色輸出至終端標準輸出（適合搭配 fzf 預覽）。
- 🔌 **Stdin Pipe**：支援由命令列管線直接輸入（如 `cat file.md | mdreader` 或 AI 工具輸出）。

## Installation

```bash
# Clone the repository
git clone https://github.com/candyz/mdreader.git
cd mdreader

# Install using pip
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
# 1. Open without arguments to browse and select Markdown files in current folder
mdreader

# 2. Preview a specific markdown file interactively (full document view by default)
mdreader README.md

# 3. Preview test.md containing complex Mermaid flowchart
mdreader test.md

# 4. Watch mode: auto-reload when file changes
mdreader -w test.md

# 5. Set specific theme on launch
mdreader -t solarized-dark test.md

# 6. Show TOC outline sidebar on startup (default is hidden)
mdreader --toc test.md

# 7. Set maximum width (columns)
mdreader --width 100 test.md

# 8. Non-interactive stdout preview
mdreader --inline test.md

# 9. Stream or pipe from stdin
cat test.md | mdreader
```

## Keybindings (TUI Mode)

| Key | Action |
| :--- | :--- |
| `q` / `Esc` | Quit viewer / Dismiss modal or search |
| `O` | **開啟大綱模式 (Outline)**：進入章節瀏覽視窗，以 ↑/↓/j/k 選擇，按 Enter 跳轉至該章節 |
| `o` | Open Fuzzy File Picker modal (檔案選擇器) |
| `Ctrl+O` | **Midnight Commander 雙欄檔案管理模式**：左右雙欄切換 (`Tab`)、`Ins`/`Space` 批次多選、`F3`/`Enter` 檢視、`F4` 編輯、`F5` 複製、`F6` 移動/重命名、`F7` 新增資料夾、`F8` 刪除、`Ctrl+O`/`Esc` 返回閱讀 |
| `v` | **開啟外部編輯器 (Edit in Vim / $EDITOR)**：離開編輯後自動重載 |
| `t` | Switch Color Theme (切換色彩主題) |
| `/` | **開啟搜尋欄 (Search)**：輸入 `/keyword` 後按 Enter 開始搜尋 |
| `n` | **Jump to Next Search Match (跳至下一處搜尋結果)** |
| `N` | **Jump to Previous Search Match (跳至上一處搜尋結果)** |
| `j` / `Page Up` | **Scroll Page Up (上一頁)** |
| `k` / `Page Down` | **Scroll Page Down (下一頁)** |
| `gg` / `Home` | **Jump to Top (回到文件最上方)** |
| `G` / `End` | **Jump to Bottom (跳至文件最下方)** |
| `Down` / `Up` | Line by line scroll (逐行垂直捲動) |
| `Left` / `Right` / `d` / `f` | Horizontal scroll (`d` 向左捲動、`f` 向右捲動) |
| `Mouse Drag` | **選取文字 (Select Text)**：框選文字時自動複製到系統剪貼簿 |
| `Shift + Drag` | **終端原生選取 (Terminal Bypass)**：強制使用終端原生框選複製 |
| `m` | **切換滑鼠攔截模式 (Toggle Mouse Mode)**：關閉時完全恢復終端原生滑鼠操作 |
| `Right Click` | **滑鼠右鍵選單 (Context Menu)**：開啟浮動選單進行 Copy / Search / Select All |
| `y` / `c` / `Ctrl+C` | **手動複製已選取文字 (Copy Selection)** |
| `-` | **收窄閱讀版面寬度 (Narrow column width)**（最窄 40 欄） |
| `=` / `+` | **拓寬閱讀版面寬度 (Widen column width)**（至 100% 滿版） |
| `Cmd +` / `Cmd -` | **縮放終端字型大小 (Terminal Font Zoom)**（由終端模擬器控制） |
| `Mouse wheel` | Scroll (滑鼠滾動) |
