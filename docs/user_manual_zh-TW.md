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
| **`o`** | **開啟檔案選擇器 (File Picker)**：`Ctrl+R` 最近檔案、`Ctrl+D` 目錄書籤、`Ctrl+F` 全文搜尋 |
| **`O`** | **開啟大綱模式 (TOC Outline)**：進入章節瀏覽視窗，以 ↑/↓/j/k 選擇，按 Enter 跳轉至該章節 |
| **`Ctrl+O`** | **Midnight Commander 雙欄檔案總管**：左右雙欄 (`Tab`)、`Ins`/`Space` 批次多選、`F3` 檢視、`F4` 編輯、`F5` 複製、`F6` 移動、`F7` 建立目錄、`F8` 刪除、`s` 排序、`Ctrl+D` 書籤、`Ctrl+F` 全文搜尋 |
| **`w`** / **`Alt+Z`** | **切換自動折行 (Toggle Soft Wrap)**：在自動折行與水平捲動模式之間切換 |
| **`L`** / **`Alt+L`** | **切換行號顯示 (Toggle Line Numbers)**：在原始碼與純文字檔案中顯示/隱藏左側行號欄 |
| **`gx`** | **擷取超連結 (Open Links)**：列出文件中的網址並於預設瀏覽器中開啟 |
| **`m` + `[a-z]`** | **建立書籤 (Set Mark)**：在當前行建立以指定英文字母命名的書籤 |
| **`'` + `[a-z]`** | **跳轉書籤 (Jump to Mark)**：立即跳轉至先前儲存的書籤行號 |
| **`Ctrl+M`** | **書籤總覽 (List Marks)**：開啟書籤清單視窗進行檢視與跳轉 |
| **`:`** / **`123G`** / **`50gg`** | **跳轉行號 (Go to Line)**：快速跳轉至指定行號 |
| **`e`** | **匯出文件 (Export)**：將目前文件匯出為獨立 HTML (.html)、純文字 (.txt) 或 Markdown (.md) |
| **`Y`** / **`Ctrl+K`** | **複製程式碼區塊 (Copy Code Block)**：快速提取並複製程式碼區塊至系統剪貼簿 |
| **`v`** | **開啟外部編輯器 (Vim / $EDITOR)**：暫停閱讀器開啟編輯器，存檔退出後自動重新載入 |
| **`Ctrl+T`** | **開啟終端機 Shell**：在當前檔案所在目錄開啟原生 Shell |
| **`Ctrl+Shift+O`** | **檔案管理員定位**：在系統檔案管理員（Finder / xdg-open）中顯示該檔案 |
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
