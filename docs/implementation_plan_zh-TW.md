# 📖 mdreader — Terminal Markdown Reader 實作規劃書

> **專案目標**：開發一款可在 Terminal 底下閱讀 Markdown 檔案的 TUI 工具，類似 [leaf](https://github.com/RivoLink/leaf) 的互動體驗，但能正確處理並渲染 Mermaid 流程圖，解決 leaf 遇到 mermaid 語法時完全無法執行的問題。

---

## 一、問題背景

### 1.1 leaf 的優點
- Rust 編寫，效能極佳
- 互動式 TUI 瀏覽體驗（捲動、主題切換、寬度調整）
- 支援 fuzzy file picker、watch mode、inline mode
- 支援語法高亮的 code block

### 1.2 leaf 的痛點
- **遇到 `mermaid` code block 時直接 crash**，無法開啟含有 mermaid 語法的 `.md` 檔案
- 以 [test.md](file:///Users/candyz/AI/agy/mdreader/test.md) 為例，該檔案包含 `graph TD` 類型的 mermaid 流程圖，leaf 完全無法開啟

### 1.3 現有替代方案分析

| 工具 | 語言 | Mermaid 支援 | 缺點 |
|:---|:---|:---|:---|
| [glow](https://github.com/charmbracelet/glow) | Go | ❌ | 無 mermaid 支援 |
| [mdr](https://github.com/CleverCloud/mdr) | Rust | ✅ (SVG) | 需要 webview 後端 |
| [mdview](https://github.com/tzachbon/mdview) | Bun/JS | ✅ (ASCII) | 需要 Bun runtime |
| **termaid** | Python | ✅ (ASCII/Unicode) | 僅處理 mermaid，不是 md reader |

**結論**：沒有一款工具同時兼具「leaf 的輕量 TUI 體驗」與「mermaid 圖表正確渲染」。自行開發是合理選擇。

---

## 二、技術選型

### 2.1 開發語言：Python

**理由**：
- `textual` 框架提供成熟的 TUI 開發能力（CSS 風格排版、事件驅動、非同步）
- `rich` 內建高品質的 Markdown 渲染（標題、列表、表格、code block 語法高亮）
- `termaid` 提供純 Python 的 mermaid → ASCII/Unicode 轉換，零外部依賴
- 三者同屬一個生態系，整合無縫

### 2.2 核心依賴

```
textual          # TUI 框架（互動介面、捲動、鍵盤/滑鼠控制）
rich             # Markdown 渲染引擎（標題、表格、code block）
termaid          # Mermaid → ASCII/Unicode 圖表轉換
```

### 2.3 為什麼不用 Rust？

leaf 用 Rust 確實效能好，但我們的核心需求是「正確渲染 mermaid」，而：
- Rust 生態缺乏成熟的 mermaid ASCII 渲染 crate
- Python 的 `textual` + `rich` 啟動速度已在 100~200ms 以內，對 md reader 來說足夠
- 開發速度快，方便後續擴充

---

## 三、功能規格

### 3.1 MVP（最小可行版本）

| 功能 | 說明 |
|:---|:---|
| **Markdown 渲染** | 標題、粗體/斜體、列表、引用、表格、水平線、連結 |
| **Code Block 語法高亮** | 依據語言標記（python, bash, sql 等）語法高亮 |
| **Mermaid 圖表渲染** | 偵測 ` ```mermaid ` 區塊，透過 termaid 轉為 ASCII/Unicode art 嵌入顯示 |
| **捲動瀏覽** | 上下鍵 / Page Up/Down / 滑鼠滾輪 |
| **退出** | `q` 或 `Esc` 退出 |

### 3.2 Phase 2 增強功能

| 功能 | 說明 |
|:---|:---|
| **目錄側欄 (TOC)** | 解析 `#` 標題自動生成目錄，點擊跳轉 |
| **搜尋** | `/` 啟動全文搜尋，高亮匹配 |
| **Watch Mode** | `--watch` / `-w` 偵測檔案變更後自動重新渲染 |
| **主題切換** | 深色/淺色主題，快捷鍵 `t` 切換 |
| **寬度控制** | `--width <n>` 控制內容最大寬度 |

### 3.3 Phase 3 進階功能

| 功能 | 說明 |
|:---|:---|
| **Fuzzy File Picker** | 無參數時啟動模糊搜尋 `.md` 檔案 |
| **Stdin Pipe** | 支援 `cat file.md \| mdreader` 或 `claude "..." \| mdreader` |
| **Inline Mode** | `--inline` 直接輸出到 stdout（非互動） |
| **iTerm2 圖片協定** | 偵測 iTerm2 環境時，mermaid 改用 mmdc → PNG → imgcat 顯示高品質圖表 |

---

## 四、架構設計

### 4.1 模組結構

```
mdreader/
├── __main__.py          # 入口：CLI 參數解析
├── app.py               # Textual App 主程式
├── widgets/
│   ├── markdown_view.py # 核心：Markdown + Mermaid 混合渲染 Widget
│   └── toc_sidebar.py   # Phase 2: 目錄側欄 Widget
├── renderer/
│   ├── markdown.py      # Markdown 渲染（基於 rich.markdown）
│   └── mermaid.py       # Mermaid 區塊偵測與轉換（基於 termaid）
├── utils/
│   └── file_watcher.py  # Phase 2: 檔案變更監聽
└── themes/
    ├── dark.tcss         # Textual CSS 深色主題
    └── light.tcss        # Textual CSS 淺色主題
```

### 4.2 核心渲染流程

```
                 ┌──────────────────────┐
                 │  讀取 .md 原始內容     │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │  解析 fenced code     │
                 │  blocks (正則匹配)     │
                 └──────────┬───────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
    ┌─────────▼─────────┐     ┌───────────▼───────────┐
    │ 一般 code block    │     │ mermaid code block     │
    │ → 保留原樣          │     │ → termaid.render()     │
    │   (rich 語法高亮)   │     │   轉為 ASCII art       │
    └─────────┬─────────┘     └───────────┬───────────┘
              │                           │
              └─────────────┬─────────────┘
                            │
                 ┌──────────▼───────────┐
                 │  替換後的完整 MD 文本   │
                 │  → rich.Markdown 渲染  │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │  Textual ScrollView   │
                 │  顯示渲染結果          │
                 └──────────────────────┘
```

### 4.3 Mermaid 渲染策略

**策略：預處理替換**

在將 Markdown 交給 `rich.Markdown` 之前，先掃描所有 ` ```mermaid ` 區塊：
1. 提取 mermaid 語法內容
2. 呼叫 `termaid.render()` 轉為 ASCII/Unicode art 文字
3. 將原始 mermaid block 替換為一般的 ` ```text ` block（內容為 ASCII art）
4. 整體交給 `rich.Markdown` 統一渲染

**fallback**：如果 termaid 轉換失敗（語法不支援等），則顯示原始 mermaid 原始碼並加上 `⚠️ Mermaid 渲染失敗` 提示，而非 crash。

---

## 五、CLI 介面設計

```bash
# 基本用法
mdreader README.md

# Watch mode
mdreader -w README.md
mdreader --watch README.md

# 指定寬度
mdreader --width 100 README.md

# 主題
mdreader --theme dark README.md

# Inline mode（非互動，直接 stdout）
mdreader --inline README.md

# Stdin pipe
cat README.md | mdreader
claude "explain async" | mdreader

# 版本
mdreader --version
```

---

## 六、分階段實作計畫

### Phase 1：MVP — 能看 MD + Mermaid（目標：可用）

```
1. 專案初始化
   ├── pyproject.toml / setup
   ├── 安裝 textual, rich, termaid
   └── 驗證：pip install -e . 成功

2. mermaid 預處理器
   ├── renderer/mermaid.py
   ├── 正則匹配 ```mermaid 區塊
   ├── 呼叫 termaid 渲染
   └── 驗證：test.md 中的 mermaid 圖表正確轉為 ASCII

3. Markdown 渲染整合
   ├── renderer/markdown.py
   ├── 先 mermaid 預處理 → 再 rich.Markdown 渲染
   └── 驗證：test.md 完整渲染，包含文字 + 表格 + mermaid 圖

4. TUI 互動介面
   ├── app.py (Textual App)
   ├── widgets/markdown_view.py (ScrollableContainer)
   ├── 鍵盤控制：↑↓ 捲動、q 退出
   └── 驗證：mdreader test.md 可互動瀏覽

5. CLI 入口
   ├── __main__.py (argparse)
   └── 驗證：mdreader test.md 從命令列啟動成功
```

**Phase 1 成功標準**：`mdreader test.md` 可正確顯示 test.md 的所有內容，包含 mermaid 圖表的 ASCII 版本，且可上下捲動瀏覽，`q` 退出。

### Phase 2：體驗提升

```
6. TOC 目錄側欄
7. 全文搜尋 (/)
8. Watch mode (-w)
9. 主題切換 (t)
10. 寬度控制 (--width)
```

### Phase 3：生態整合

```
11. Fuzzy file picker
12. Stdin pipe 支援
13. Inline mode (--inline)
14. iTerm2 圖片協定 mermaid 高品質渲染
```

---

## 七、風險與對策

| 風險 | 影響 | 對策 |
|:---|:---|:---|
| termaid 不支援某些 mermaid 語法 | 部分圖表無法渲染 | Graceful fallback：顯示原始碼 + 警告訊息 |
| rich.Markdown 不支援某些 MD 語法 | 部分元素顯示異常 | 已知限制：HTML 標籤、腳註等，文件中註明 |
| textual 啟動速度不如 Rust | 體感稍慢 | 實測約 100~200ms，可接受；必要時 lazy import |
| mermaid 圖表過大撐爆終端寬度 | 排版錯亂 | 根據終端寬度自動截斷或水平捲動 |

---

## 八、驗收標準
 
 以 [test.md](file:///Users/candyz/AI/agy/mdreader/test.md) 作為驗收測試檔案：
 
 - [x] 標題（`#` ~ `######`）正確渲染為不同大小/樣式
 - [x] 表格正確對齊顯示
 - [x] Code block 有語法高亮（SQL, scheme, bash）
 - [x] **Mermaid `graph TD` 流程圖正確轉為 ASCII art 顯示**
 - [x] 上下與水平左右捲動流暢（`↑`/`↓`/`←`/`→`/`j`/`k`/`gg`/`G`）
 - [x] `Tab` 開啟專屬大綱瀏覽視窗 (Outline Modal)，選擇後跳轉
 - [x] `/` Vim 風格全文搜尋與 `n` / `N` 跳轉
 - [x] `v` 呼叫外部編輯器 (`$EDITOR` / `vim`) 並在退出後自動重載
 - [x] `q` / `Esc` 可正常退出
 - [x] 不會因任何 mermaid 語法而 crash
