# mdreader — Terminal Markdown Reader

An interactive terminal Markdown previewer with native **Mermaid flowchart rendering** support (GUI-like experience in CLI), inspired by [leaf](https://github.com/RivoLink/leaf).

## Features

- 📑 **Rich Markdown Rendering**: Headers, tables, lists, quotes, styled code blocks.
- 🌐 **HTML Document Support**: Native rendering for `.html` / `.htm` web documents and piped HTML with tables, headings, code, and lists.
- 📊 **Mermaid Flowchart Support**: Automatically renders ```` ```mermaid ```` diagrams as ASCII/Unicode art inline without crashing.
- 📑 **Interactive Table of Contents (TOC)**: Automatically extracts document headings into a clickable / keyboard-navigable sidebar (`Tab` to toggle).
- 📂 **Fuzzy File Picker**: Interactive modal file selector with instant filtering (`o` key in TUI or launch `mdreader` without arguments).
- 🔄 **Watch Mode**: Live hot-reloading on disk changes (`-w` / `--watch`).
- 🎨 **Multi-Theme Support**: Built-in dark/light/retro color themes (`t` to switch in-app or `-t` flag).
- 🔍 **In-document Search Bar**: Quick search overlay triggered with `/`.
- 🖼️ **Terminal Graphics Protocol Ready**: iTerm2 / Kitty inline image protocol integration.
- ⚡ **Interactive TUI**: Maximized reading screen (clean viewport with clock in bottom bar), smooth scrolling, custom width (`--width`), vim keybindings (`j`/`k`/`gg`/`G`/`q`/`Esc`).
- 📟 **Inline Mode**: Pipe directly to terminal with ANSI colors via `--inline`.
- 🔌 **Stdin Pipe**: Supports piping directly from CLI tools (e.g. `cat file.md | mdreader` or AI tools).

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
| `Tab` | **開啟大綱模式 (Outline)**：進入章節瀏覽視窗，以 ↑/↓/j/k 選擇，按 Enter 跳轉至該章節 |
| `o` | Open Fuzzy File Picker modal (檔案選擇器) |
| `F9` / `Ctrl+O` | **Midnight Commander 雙欄檔案管理模式**：左右雙欄切換 (`Tab`)、`F3`/`Enter` 檢視、`F4` 編輯、`F9`/`Esc` 返回閱讀 |
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
