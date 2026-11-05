# 📊 mdreader — Office File Formats (Word / PowerPoint / Excel) Feasibility & Implementation Plan

[繁體中文版 (Traditional Chinese)](office_support_plan_zh-TW.md)

> **Objective**: Evaluate the feasibility and design a surgical implementation plan for adding Microsoft Office file format support (Word `.docx`/`.doc`, PowerPoint `.pptx`/`.ppt`, Excel `.xlsx`/`.xls`/`.csv`) to `mdreader` while preserving its lightweight footprint, cross-platform compatibility (macOS & Linux), and Python 3.9 ~ 3.14+ support.

---

## 1. Executive Summary

- **Feasibility Rating**: **High** — Naturally aligns with `mdreader`'s existing preprocessing pipeline.
- **Core Architectural Strategy**: **"Convert Office Documents to Structured GFM Markdown → Reuse Existing Rendering & Navigation Engine"**
  `mdreader` already uses this exact pattern for HTML files via `html_to_markdown()` in [`src/mdreader/renderer/html.py`](../src/mdreader/renderer/html.py).
- **Immediate Feature Inheritance (Zero Extra Widget Code)**:
  By converting `.docx`, `.pptx`, and `.xlsx` into structured GFM Markdown at load time, Office documents immediately inherit all existing `mdreader` capabilities:
  1. **Viewport-Aware Table Wrapping**: Inherits v1.8.1's `fit_table_col_sizes()` for automatic CJK/text wrapping in WRAP mode and horizontal scrolling (`h`/`l`) in NOWRAP mode.
  2. **Outline / TOC Quick Jump (`O` / Sidebar)**:
     - Word `Heading 1 ~ 6` map directly to `# ~ ######`.
     - PowerPoint slides map to `## 📽️ Slide N: <Title>`, enabling instant slide jumping via the Outline modal.
     - Excel worksheets map to `## 📊 Sheet: <Name>`, enabling instant switching between sheets.
  3. **Full-Text Search & Marks**: `/` in-document search and `m`/`'` Vim marks work out of the box.
  4. **HTML Export & CLI Inline Mode**: `e` / `--export-html` and `--inline` work seamlessly on Office files.

---

## 2. Constraints & Library Selection

### 2.1 Hard Project Constraints
1. **Python 3.9 ~ 3.14+ Compatibility**:
   Cluster nodes include Rocky Linux 9 (`Python 3.9.25`) as well as Ubuntu 26.04.1 and macOS (`Python 3.14+`). Any library requiring `python >= 3.10` is strictly disqualified.
2. **Zero Mandatory System Binaries**:
   Must install cleanly via `pipx` or `uv tool` on headless Linux servers without requiring LibreOffice or Pandoc.

### 2.2 Library Comparison

| Approach | Libraries | Python 3.9 Support | Footprint | Fidelity | Verdict |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Option A (Recommended): Dedicated Pure-Python Libraries + Stdlib OOXML Fallback** | `python-docx` + `python-pptx` + `openpyxl` (plus stdlib `zipfile` + `xml.etree` fallback) | ✅ Yes (3.7~3.14) | Lightweight (~5MB) | ⭐⭐⭐⭐⭐ | **Selected**. Fast installation, full control over table/heading/slide formatting. |
| **Option B: Microsoft `markitdown`** | `markitdown` | ❌ **No** (Requires >=3.10) | Heavy (>100MB) | ⭐⭐⭐⭐ | **Rejected**. Breaks Python 3.9 compatibility on Rocky Linux 9 nodes. |
| **Option C: External System Binaries** | `pandoc` / `libreoffice` / `antiword` | ✅ OS-dependent | Huge (500MB+) | ⭐⭐⭐ | **Optional fallback only** for legacy binary `.doc` / `.ppt` files. |

---

## 3. Format Conversion Specifications (`src/mdreader/renderer/office.py`)

### 3.1 Word (`.docx`, optional `.doc`)
- **Headings**: `Heading 1~6` → `#` ~ `######`.
- **Inline Formatting**: Bold (`**`), Italic (`*`), inline code, and hyperlinks (`[text](url)`).
- **Lists**: Bullet and numbered lists with nesting depth mapped to standard Markdown lists.
- **Tables**: Converted to GFM pipe tables (`| H1 | H2 |`).
- **Legacy `.doc`**: Auto-detect `textutil -convert txt -stdout` (built-in on macOS), `antiword`, or `soffice` if available; otherwise display a clear conversion hint.

### 3.2 PowerPoint (`.pptx`)
- **Slide Sections**: Each slide becomes a level-2 heading (`## 📽️ Slide N: <Slide Title>`) separated by `---`.
- **Text Frames**: Bullet hierarchies indented according to paragraph `level`.
- **Slide Tables**: Converted to GFM pipe tables.
- **Speaker Notes**: Rendered as blockquotes (`> 📝 **Notes**: ...`) at the bottom of each slide.

### 3.3 Excel (`.xlsx`, `.xls`, `.csv`, `.tsv`)
- **Streaming Value Read**: Uses `openpyxl.load_workbook(filepath, read_only=True, data_only=True)` to read evaluated formula values with minimal RAM.
- **Sheet Sections**: Each non-empty sheet becomes `## 📊 Sheet: <Name> (R rows × C cols)`.
- **Empty Boundary Trimming**: Automatically strips trailing empty rows and columns.
- **Large Sheet Safeguard**: Caps GFM table rendering at 500 rows per sheet by default (with a summary footer), and routes files exceeding `LARGE_FILE_LINE_THRESHOLD (5000)` to `VirtualTextViewer`.

---

## 4. Surgical Codebase Integration Points

| File | Changes | Purpose |
| :--- | :--- | :--- |
| `src/mdreader/renderer/office.py` *(New)* | Implement `is_office_file()`, `get_office_type_label()`, and `office_to_markdown()` | Core Office-to-Markdown conversion |
| [`pyproject.toml`](../pyproject.toml) | Add `python-docx>=1.1.0`, `python-pptx>=0.6.23`, `openpyxl>=3.1.0` | Lightweight Python 3.9+ compatible parsers |
| [`src/mdreader/app.py`](../src/mdreader/app.py) | Route `is_office_file(filepath)` through `office_to_markdown(filepath)` instead of `read_text(encoding="utf-8")`; show `Word`/`PowerPoint`/`Excel` in StatusBar | Prevent `UnicodeDecodeError` on binary Office files and render as Markdown |
| [`src/mdreader/__main__.py`](../src/mdreader/__main__.py) | Support `is_office_file()` in CLI direct open, `--inline`, and `--export-html` | Full CLI support |
| [`src/mdreader/widgets/file_picker.py`](../src/mdreader/widgets/file_picker.py) | Add `.docx`, `.doc`, `.pptx`, `.xlsx`, `.xls`, `.csv`, `.tsv` to `supported_exts` with icons `📘`, `📙`, `📗` | Native visibility in `o` Fuzzy File Picker |
| [`src/mdreader/widgets/virtual_viewer.py`](../src/mdreader/widgets/virtual_viewer.py) | Treat converted Office content like Markdown in `should_use_virtual_viewer()` | Render tables/headings via `MarkdownViewerWidget` unless >5000 lines |

---

## 5. Phased Rollout & Verification

1. **Phase 1**: Implement `src/mdreader/renderer/office.py` (with both library parsers and stdlib `zipfile + xml` fallback) and unit tests in `tests/test_office_renderer.py`.
2. **Phase 2**: Integrate with `app.py`, `__main__.py`, `file_picker.py`, and `virtual_viewer.py`; verify table wrapping, TOC navigation, and status bar badges in headless Textual tests.
3. **Release**: Bump minor version (`1.8.4` → `1.9.0` per Rule 15) and update documentation.
