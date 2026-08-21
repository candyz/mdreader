# 📖 mdreader — Terminal Markdown Reader Implementation Plan

[繁體中文版 (Traditional Chinese)](implementation_plan_zh-TW.md)

> **Project Goal**: Build a lightweight, interactive Terminal Markdown & HTML viewer inspired by [leaf](https://github.com/RivoLink/leaf), with first-class **Mermaid flowchart rendering** support to resolve the crash issue leaf experiences with mermaid blocks.

---

## 1. Problem Background

### 1.1 Strengths of leaf
- Written in Rust with excellent performance.
- Rich interactive TUI browsing experience (scrolling, theme switching, width adjustment).
- Supports fuzzy file picker, watch mode, and inline mode.
- Syntax-highlighted code blocks.

### 1.2 Pain Points of leaf
- **Crashes immediately on `mermaid` code blocks**, rendering files with mermaid syntax unreadable.
- For example, opening test files with `graph TD` diagrams completely fails.

### 1.3 Alternative Solutions Comparison

| Tool | Language | Mermaid Support | Drawback |
| :--- | :--- | :--- | :--- |
| [glow](https://github.com/charmbracelet/glow) | Go | ❌ | No mermaid support |
| [mdr](https://github.com/CleverCloud/mdr) | Rust | ✅ (SVG) | Requires webview backend |
| [mdview](https://github.com/tzachbon/mdview) | Bun/JS | ✅ (ASCII) | Requires Bun runtime |
| **termaid** | Python | ✅ (ASCII/Unicode) | Standalone renderer, not a full md reader |

**Conclusion**: Building `mdreader` in Python with Textual + Rich + Termaid offers the ideal balance of lightweight TUI and flawless ASCII Mermaid rendering.

---

## 2. Technical Stack

### 2.1 Language: Python (3.9 ~ 3.14)
- `textual`: Mature TUI framework (reactive architecture, CSS layout, keyboard/mouse events).
- `rich`: High-quality terminal markdown renderer (tables, quotes, code blocks).
- `termaid`: Pure Python Mermaid → ASCII/Unicode diagram transformer.
- Standard Library `html.parser`: Zero-dependency HTML to Markdown converter.

---

## 3. Architecture & Rendering Pipeline

```
                 ┌───────────────────────────┐
                 │  Read .md / .html Source  │
                 └─────────────┬─────────────┘
                               │
                 ┌─────────────▼─────────────┐
                 │  HTML to Markdown Parser  │
                 └─────────────┬─────────────┘
                               │
                 ┌─────────────▼─────────────┐
                 │  Mermaid Preprocessor     │
                 │  (termaid ASCII render)   │
                 └─────────────┬─────────────┘
                               │
                 ┌─────────────▼─────────────┐
                 │  Textual MarkdownViewer   │
                 │  (Interactive TUI Engine) │
                 └───────────────────────────┘
```

---

## 4. Verification Checklist

- [x] Headers (`#` ~ `######`) rendered with distinct styles.
- [x] Tables aligned and styled cleanly.
- [x] Code blocks with syntax highlighting.
- [x] **Mermaid `graph TD` / `graph LR` converted to ASCII art**.
- [x] Smooth vertical and horizontal scrolling (`↑`/`↓`/`←`/`→`/`j`/`k`/`gg`/`G`).
- [x] `Tab` opens Table of Contents outline modal for instant navigation.
- [x] `/` Vim-style in-document search with `n` / `N` navigation.
- [x] `v` suspends TUI to edit in external `$EDITOR` / `vim` with auto-reload.
- [x] `m` toggles mouse tracking for native terminal text selection.
- [x] Native HTML document rendering (`.html` / `.htm`).
