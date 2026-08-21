# 📖 mdreader 使用者操作手冊 (User Manual)

**mdreader** 是一款專為 Terminal / CLI 開發者設計的 Markdown 檔案閱讀器，具備現代化純淨全螢幕 TUI 介面（移除頂部無效標題列以最大化閱讀空間，時間顯示於底端列最右側），並原生支援 **Mermaid 流程圖轉 ASCII 視覺化渲染**，徹底解決傳統工具（如 leaf）遇到 mermaid 語法會崩潰報錯的問題。

---

## 🎯 快速開始 (Quick Start)

### 1. 開啟 Markdown 檔案
```bash
# 開啟指定文件
mdreader README.md
mdreader docs/implementation_plan.md
```

### 2. 無參數啟動（自動模糊搜尋檔案）
若沒有提供參數，mdreader 會自動搜尋當前目錄與子目錄下的所有 `.md` 檔案供您選擇：
```bash
mdreader
```

### 3. 熱重載監聽模式 (Watch Mode)
在撰寫文件或筆記時，搭配編輯器開啟 watch 模式，每次存檔時終端畫面會即時自動更新：
```bash
mdreader -w README.md
mdreader --watch docs/deployment_guide.md
```

---

## ⌨️ 鍵盤操作與快捷鍵 (Keybindings)

在互動式 TUI 介面中，可使用以下鍵盤快捷鍵進行高效導航：

| 快捷鍵 | 功能說明 |
| :--- | :--- |
| **`q`** / **`Esc`** | 退出 mdreader 閱讀器 / 關閉目前浮動視窗 |
| **`Tab`** | **開啟大綱模式 (TOC Outline)**：進入章節瀏覽視窗，以 ↑/↓/j/k 選擇，按 Enter 跳轉至該章節 |
| **`j`** / **`Page Up`** | **整頁向上翻頁 (Page Up)** |
| **`k`** / **`Page Down`** | **整頁向下翻頁 (Page Down)** |
| **`gg`** / **`Home`** | **回到文件最上方 (Jump to Top)** |
| **`G`** / **`End`** | **跳至文件最下方 (Jump to Bottom)** |
| **`↓`** / **`↑`** | 逐行平滑向上 / 向下垂直捲動 |
| **`←`** / **`→`** | **向左 / 向右水平捲動**（當代碼區塊或表格太寬超出螢幕時使用） |
| **`o`** | **開啟模糊檔案選擇器 (File Picker)**，隨時切換不同文件 |
| **`v`** | **開啟外部編輯器 (Vim / $EDITOR)**：暫停閱讀器開啟編輯器，存檔退出後自動重新載入 |
| **`t`** | **循環切換主題色彩**（深色/淺色/Tokyo Night/Monokai 等） |
| **`/`** | **開啟文件內搜尋欄**（輸入 `/關鍵字` 後按 Enter 立即開始搜尋） |
| **`n`** | **跳至下一處搜尋結果 (Next Match)** |
| **`N`** | **跳至上一處搜尋結果 (Previous Match)** |
| **滑鼠滾輪** | 自由滾動內容 |

---

## 📝 外部編輯器整合 (Edit with Vim)

在閱讀 Markdown 文件時，隨時可按 **`v`** 鍵直接調用終端編輯器修改文件：
- **環境變數支援**：優先讀取系統 `$EDITOR` 或 `$VISUAL`（預設為 `vim`，找不到時依序 fallback 至 `vi` / `nano`）。
- **無縫暫停與恢復**：mdreader 會自動暫停 TUI 畫面並進入編輯器，待編輯完成存檔退出（如 `:wq`）後，自動恢復並**即時重新載入最新內容（包含 Mermaid 圖表重新渲染）**。

---

## ⚙️ 進階指令參數與使用場景

### 1. 指定介面色彩主題 (`-t` / `--theme`)
啟動時可直接指定主題配色：
```bash
mdreader -t tokyo-night README.md
mdreader -t solarized-dark README.md
mdreader -t textual-light README.md
```
> 支援主題：`textual-dark`, `textual-light`, `tokyo-night`, `monokai`, `solarized-dark`, `solarized-light`, `catppuccin-frappe`, `catppuccin-latte`, `dracula`, `nord`。

### 2. 限制文件最大閱讀寬度 (`--width`)
在高解析度寬螢幕終端下，可限制閱讀寬度以提升排版可讀性：
```bash
mdreader --width 100 README.md
```

### 3. 啟動時預設顯示大綱目錄側欄 (`--toc`)
預設進入為滿版全文件閱讀模式；若希望啟動時立即開啟目錄導航側欄，可加上 `--toc`（進入後亦可隨時按 `Tab` 切換）：
```bash
mdreader --toc README.md
```

### 4. 非互動輸出模式 (`--inline`)
不進入 TUI，直接將渲染後的 ANSI 帶色彩格式輸出至 Terminal 標準輸出（適合於腳本或 fzf 預覽）：
```bash
mdreader --inline README.md

# 搭配 fzf 進行文件即時預覽
fzf --preview 'mdreader --inline {}'
```

### 5. Stdin 管道串接 (Pipe)
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
