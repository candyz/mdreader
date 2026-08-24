# 📖 mdreader 使用者操作手冊 (User Manual)

**mdreader** 是一款專為 Terminal / CLI 開發者設計的 Markdown、HTML 與原始碼檔案閱讀器，具備現代化純淨全螢幕 TUI 介面、GB 級超大檔案隨選讀取架構，並原生支援 **Mermaid 流程圖轉 ASCII 視覺化渲染**，徹底解決傳統工具（如 leaf）遇到 mermaid 語法會崩潰報錯的問題。

---

## 🎯 快速開始 (Quick Start)

### 1. 開啟 Markdown、HTML 或原始碼檔案
```bash
# 開啟 Markdown 文件並直接跳轉至第 50 行
mdreader +50 README.md
mdreader -l 50 README.md

# 開啟 HTML 網頁文件（自動轉譯並保留大綱與排版）
mdreader index.html

# 開啟巨量純文字或 Log 資料檔（自動啟用 mmap 極速隨選讀取）
mdreader gigantic_data.log
```

### 2. 無參數啟動（自動模糊搜尋檔案）
若沒有提供參數，mdreader 會自動開啟檔案選擇器供您挑選檔案：
```bash
mdreader
```

### 3. 熱重載監聽模式 (Watch Mode)
在撰寫文件、網頁或筆記時，搭配編輯器開啟 watch 模式，每次存檔時終端畫面會即時自動更新：
```bash
mdreader -w README.md
mdreader --watch index.html
```

### 4. 無介面直接匯出 (Headless Export)
無須進入 TUI 畫面，直接在終端命令列將文件轉換為獨立 HTML 或純文字檔：
```bash
mdreader README.md --export-html output.html
mdreader README.md --export-txt output.txt
```

---

## ⌨️ 鍵盤操作與快捷鍵 (Keybindings)

在互動式 TUI 介面中，可使用以下鍵盤快捷鍵進行高效導航：

| 快捷鍵 | 功能說明 |
| :--- | :--- |
| **`q`** / **`Esc`** | 退出 mdreader 閱讀器 / 關閉目前浮動視窗 |
| **`h`** / **`?`** / **`F1`** | **快速鍵與功能說明 (Help)**：開啟完整快速鍵指南對話框 |
| **`o`** | **開啟檔案選擇器 (File Picker)**：`Ctrl+R` 最近檔案、`Ctrl+D` 目錄書籤、`Ctrl+F` 全文搜尋 |
| **`O`** | **開啟大綱模式 (TOC Outline)**：進入章節瀏覽視窗，以 ↑/↓/j/k 選擇，按 Enter 跳轉至該章節 |
| **`Ctrl+O`** | **Midnight Commander 雙欄檔案總管**：左右雙欄 (`Tab`)、`Ins`/`Space` 批次多選、`F3` 檢視、`F4` 編輯、`F5` 複製、`F6` 移動、`F7` 建立目錄、`F8` 刪除、`s` 排序、`Ctrl+D` 書籤、`Ctrl+F` 全文搜尋 |
| **`w`** / **`Alt+Z`** | **切換自動折行 (Toggle Soft Wrap)**：在自動折行與水平捲動模式之間切換 |
| **`L`** / **`Alt+L`** | **切換行號顯示 (Toggle Line Numbers)**：在原始碼與純文字檔案中顯示/隱藏左側行號欄 |
| **`gx`** | **擷取超連結 (Open Links)**：列出文件中的網址並於預設瀏覽器中開啟 |
| **`M` + `[a-z]`** | **建立書籤 (Set Mark)**：在當前行建立以指定英文字母命名的書籤 |
| **`'` + `[a-z]`** | **跳轉書籤 (Jump to Mark)**：立即跳轉至先前儲存的書籤行號 |
| **`Ctrl+M`** | **書籤總覽 (List Marks)**：開啟書籤清單視窗進行檢視與跳轉 |
| **`:`** / **`123G`** / **`50gg`** | **跳轉行號 (Go to Line)**：快速跳轉至指定行號 |
| **`e`** | **匯出文件 (Export)**：將目前文件匯出為獨立 HTML (.html)、純文字 (.txt) 或 Markdown (.md) |
| **`Y`** / **`Ctrl+K`** | **複製程式碼區塊 (Copy Code Block)**：快速提取並複製程式碼區塊至系統剪貼簿 |
| **`v`** / **`F4`** | **外部編輯器編輯 (Edit in Editor)**：暫停閱讀器，呼叫 `$EDITOR` 或 `vim` 進行編輯，儲存離開後自動熱重載 |
| **`Ctrl+T`** | **開啟終端機 (Terminal)**：在當前檔案所在目錄開啟原生 `$SHELL` 終端機環境 |
| **`T`** | **終端命令提示列 (Toggle Terminal Prompt)**：在狀態列上方展開/收合 Midnight Commander 風格的 Shell Prompt 輸入列，直接輸入指令執行 |
| **`Ctrl+Shift+O`** | **檔案管理員定位 (Reveal in Finder)**：在系統檔案管理員（Finder / xdg-open）中開啟所在位置 |
| **`t`** | **循環切換主題色彩**（Dark, Light, Tokyo Night, Monokai, Solarized, Dracula 等，自動持久化記憶） |
| **`j`** / **`Page Up`** | **整頁向上翻頁 (Page Up)** |
| **`k`** / **`Page Down`** | **整頁向下翻頁 (Page Down)** |
| **`gg`** / **`Home`** | **回到文件最上方 (Jump to Top)** |
| **`G`** / **`End`** | **跳至文件最下方 (Jump to Bottom)** |
| **`↓`** / **`↑`** | 逐行平滑向上 / 向下垂直捲動 |
| **`←`** / **`→`** / **`d`** / **`f`** | **向左 / 向右水平捲動**（`d` 向左、`f` 向右，當關閉折行時使用） |
| **`/`** | **開啟文件內搜尋欄**（輸入 `/關鍵字` 後按 Enter 立即開始搜尋） |
| **`n`** | **跳至下一處搜尋結果 (Next Match)** |
| **`N`** | **跳至上一處搜尋結果 (Previous Match)** |
| **`滑鼠拖曳`** | **自由選取文字 (Mouse Select Text)**：放開滑鼠時自動複製選取文字到系統剪貼簿 |
| **`Shift + 拖曳`** | **終端原生強制選取 (Terminal Native Bypass)**：強制使用 GNOME / macOS 終端原生框選複製 |
| **`m`** | **切換滑鼠模式 (Toggle Mouse Mode)**：一鍵開關 TUI 滑鼠事件捕捉，關閉時完全恢復終端原生選取模式 |
| **`y`** / **`c`** / **`Ctrl+C`** | **複製選取文字或全文 (Copy to Clipboard)**：無框選時自動複製全文 |
| **`-`** / **`=`** | **調整閱讀版面寬度 (Adjust Width)** |
| **滑鼠滾輪** | 自由滾動內容 |

---

## ⚙️ 進階指令參數與使用場景

### 1. 行號跳轉 (`+<line>` / `-l <line>`)
```bash
mdreader +100 README.md
mdreader -l 100 README.md
```

### 2. 列出可用主題並指定配色 (`-t` / `--list-themes`)
```bash
# 列出所有支援的配色主題
mdreader --list-themes

# 啟動時套用指定主題
mdreader -t tokyo-night README.md
```

### 3. 非互動輸出模式 (`--inline`)
不進入 TUI，直接將渲染後的 ANSI 帶色彩格式輸出至 Terminal 標準輸出（適合於腳本或 fzf 預覽）：
```bash
mdreader --inline README.md

# 搭配 fzf 進行文件即時預覽
fzf --preview 'mdreader --inline {}'
```

### 4. Stdin 管道串接 (Pipe)
支援接收來自其他指令的輸出：
```bash
cat README.md | mdreader

# 串接 AI CLI 或其他工具輸出
echo -e "# 測試標題\n\`\`\`mermaid\ngraph LR\nA --> B\n\`\`\`" | mdreader
```

---

## ⚙️ 自訂鍵盤快速鍵 (`~/.config/mdreader/config.json`)

mdreader 支援透過使用者設定檔 `~/.config/mdreader/config.json` 自由定義與覆蓋所有鍵盤快速鍵。

### 1. 設定檔格式範例

```json
{
  "theme": "github-dark",
  "keybindings": {
    "quit": ["q", "escape"],
    "open_file_picker": "o",
    "toggle_toc": "O",
    "open_commander": "ctrl+o",
    "toggle_wrap": ["w", "alt+z"],
    "edit_in_editor": ["v", "f4"],
    "toggle_theme": "t",
    "open_help": ["h", "?", "f1"],
    "open_search": "/",
    "open_goto_line": ":",
    "page_down": ["pagedown", "d", "ctrl+f"],
    "page_up": ["pageup", "u", "ctrl+b"],
    "scroll_down": ["down", "j"],
    "scroll_up": ["up", "k"],
    "zoom_in": ["+", "=", "z"],
    "zoom_out": ["-", "Z"],
    "reset_zoom": "0"
  }
}
```

### 2. 常用操作風格預設範例

#### 🅰️ Vim 重度使用者風格 (Vim-centric)
```json
{
  "keybindings": {
    "page_down": ["ctrl+f", "ctrl+d", "pagedown"],
    "page_up": ["ctrl+b", "ctrl+u", "pageup"],
    "scroll_down": ["j", "down"],
    "scroll_up": ["k", "up"],
    "scroll_left": ["h", "left"],
    "scroll_right": ["l", "right"],
    "scroll_end": "G",
    "open_search": "/",
    "open_goto_line": ":"
  }
}
```

#### 🅱️ Emacs 使用者風格 (Emacs-centric)
```json
{
  "keybindings": {
    "page_down": ["ctrl+v", "pagedown"],
    "page_up": ["alt+v", "pageup"],
    "scroll_down": ["ctrl+n", "down"],
    "scroll_up": ["ctrl+p", "up"],
    "scroll_left": ["ctrl+b", "left"],
    "scroll_right": ["ctrl+f", "right"],
    "open_file_picker": "ctrl+x ctrl+f",
    "quit": ["ctrl+x ctrl+c", "q"]
  }
}
```

### 3. 可設定之 Action 動作名稱完整一覽

| Action 動作識別碼 | 預設按鍵 | 說明 |
| :--- | :--- | :--- |
| `quit` | `q` | 離開閱讀器 |
| `open_file_picker` | `o` | 開啟檔案選擇器 |
| `toggle_toc` | `O` | 章節大綱目錄 (TOC) |
| `open_commander` | `ctrl+o` | Midnight Commander 雙欄檔案總管 |
| `toggle_wrap` | `w`, `alt+z` | 切換自動折行 |
| `edit_in_editor` | `v`, `f4` | 呼叫外部編輯器 / 系統看圖軟體 |
| `toggle_theme` | `t` | 切換色彩主題 |
| `open_help` | `h`, `?`, `f1` | 開啟說明視窗 |
| `handle_escape` | `escape` | 取消 / 關閉浮動視窗 |
| `open_search` | `/` | 文件內搜尋 |
| `open_goto_line` | `:` | 跳轉指定行號 |
| `search_next` | `n` | 下一處搜尋結果 |
| `search_prev` | `N` | 上一處搜尋結果 |
| `page_up` | `j` | 整頁向上翻頁 |
| `page_down` | `k` | 整頁向下翻頁 |
| `scroll_up` | `up` | 向上捲動 |
| `scroll_down` | `down` | 向下捲動 |
| `scroll_left` | `left`, `d` | 向左水平捲動 (看圖或關閉折行) |
| `scroll_right` | `right`, `f` | 向右水平捲動 |
| `scroll_end` | `G` | 跳至文件底部 |
| `zoom_in` | `=`, `+`, `z` | 放大閱讀版面 / 圖片 |
| `zoom_out` | `-`, `Z` | 縮小閱讀版面 / 圖片 |
| `reset_zoom` | `0` | 重設縮放比例為 100% |
| `export_document` | `e` | 匯出文件 (HTML/Text/Markdown) |
| `copy_code_block` | `Y`, `ctrl+k` | 複製程式碼區塊 |
| `copy_selected_text`| `y`, `c`, `ctrl+c`, `ctrl+y` | 複製選取文字或全文 |
| `toggle_mouse_mode` | `m` | 切換滑鼠選取模式 |
| `toggle_cmd_prompt` | `T` | 切換終端命令提示列 |
| `open_in_terminal` | `ctrl+t` | 開啟終端機 Shell |
| `reveal_in_finder` | `ctrl+shift+o` | 系統檔案管理員中定位 |
| `toggle_line_numbers`| `L`, `alt+l` | 切換行號欄顯示 |
| `reload_file` | `r` | 手動重新載入檔案 |

---

## 📊 Mermaid 流程圖支援說明

mdreader 會自動掃描 Markdown 中的 ```` ```mermaid ```` 區塊並透過 ASCII/Unicode 演算法轉譯為字元圖表：

- **支援圖表類型**：`graph TD` (流程圖)、`graph LR`、`flowchart`、`stateDiagram` 等。
- **錯誤防護 (Fault Tolerance)**：若圖表包含不支援的特殊語法，系統會自動轉換為警告區塊並保留原始代碼，絕不造成程式閃退或崩潰。

---

## ❓ 常見問題排查 (Troubleshooting)

1. **中文顯示或圖表邊框對齊問題**：
   - 請確認終端機字型支援 Nerd Fonts 或標準全形/半形等寬字型（如 JetBrains Mono、FiraCode 或 macOS SF Mono）。
2. **終端機色彩顯示異常**：
   - 請確認環境變數 `export COLORTERM=truecolor` 或終端機已啟用 24-bit True Color 支援。
3. **Linux / GNOME Terminal 剪貼簿無法貼上問題**：
   - Linux X11/Wayland 桌面環境仰賴系統剪貼簿工具。若在純乾淨的 Linux 環境下無法貼上，請安裝剪貼簿工具：
     - Ubuntu / Debian: `sudo apt install xclip` 或 `sudo apt install wl-clipboard` (Wayland)
     - Rocky / RHEL: `sudo dnf install xclip`
