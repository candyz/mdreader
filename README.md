# mdreader — Terminal Markdown Reader

[繁體中文版 (Traditional Chinese)](README_zh-TW.md)

An interactive terminal Markdown and HTML previewer with native **Mermaid flowchart rendering** support (GUI-like experience in CLI), inspired by [leaf](https://github.com/RivoLink/leaf).

---

## ✨ Features

- 📑 **Rich Markdown Rendering**: Headers, tables, lists, blockquotes, styled code blocks with syntax highlighting.
- 🌐 **Native HTML Document Support**: Zero-dependency rendering for `.html` / `.htm` web pages and piped HTML with tables, headings, code, and lists.
- 📊 **Mermaid Flowchart Support**: Automatically renders ```` ```mermaid ```` diagrams as ASCII/Unicode art inline without crashing.
- 📑 **Interactive Table of Contents (TOC Outline)**: Automatically extracts document headings into a searchable and keyboard-navigable outline modal (`Tab` to toggle).
- 📂 **Fuzzy File Picker**: Interactive modal file selector with instant filtering (`o` key in TUI or launch `mdreader` without arguments).
- 🔄 **Watch Mode**: Live hot-reloading on disk changes (`-w` / `--watch`).
- 🎨 **Multi-Theme Support**: Built-in 10+ dark/light/retro color themes (`t` to switch in-app or `-t` flag).
- 🔍 **In-document Search Bar**: Vim-style search overlay (`/`) with instant keyword jumping (`n` / `N`) and active match highlighting.
- 📝 **External Editor Integration**: Press `v` to edit with `$EDITOR` or `vim` and auto-reload upon exit.
- 🖱️ **Mouse Text Selection & Clipboard Sync**: Seamlessly copy selected text to system clipboard (supports macOS `pbcopy`, Linux X11 `xclip`, Wayland `wl-copy`, and Textual OSC 52).
- 🖲️ **Mouse Tracking Toggle**: Press `m` to toggle mouse tracking and restore native terminal text selection.
- ⚡ **Interactive TUI**: Maximized reading screen (clean viewport with clock in bottom bar), smooth scrolling, custom width adjustment (`-`/`=`), vim keybindings (`j`/`k`/`gg`/`G`/`q`/`Esc`).
- 📟 **Inline Mode**: Pipe directly to terminal standard output with ANSI colors via `--inline`.
- 🔌 **Stdin Pipe**: Supports piping directly from CLI tools (e.g. `cat file.md | mdreader` or AI tools).

---

## 🚀 Installation

### Option 1: Standard Installation via pipx (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/candyz/mdreader.git
cd mdreader

# 2. Install using pipx (isolated environment & auto-added to PATH)
pipx install .

# 3. Verify installation
mdreader --version
```

### Option 2: Development / Virtual Environment

```bash
git clone https://github.com/candyz/mdreader.git
cd mdreader
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## 🎯 Usage

```bash
# 1. Open without arguments to browse and select Markdown/HTML files in current folder
mdreader

# 2. Preview a specific markdown file interactively
mdreader README.md

# 3. Preview HTML document
mdreader index.html

# 4. Preview test.md containing complex Mermaid flowchart
mdreader test.md

# 5. Watch mode: auto-reload when file changes on disk
mdreader -w README.md

# 6. Set specific theme on launch
mdreader -t solarized-dark README.md

# 7. Show TOC outline sidebar on startup (default is hidden)
mdreader --toc README.md

# 8. Set maximum width (columns)
mdreader --width 100 README.md

# 9. Non-interactive stdout preview (ideal for fzf previewer)
mdreader --inline README.md

# 10. Stream or pipe from stdin
cat test.md | mdreader
curl -s https://example.com | mdreader
```

---

## ⌨️ Keybindings (TUI Mode)

| Key | Action |
| :--- | :--- |
| `q` / `Esc` | Quit viewer / Dismiss modal or search |
| `Tab` | **Open Table of Contents (Outline)**: Navigate chapters with `↑`/`↓`/`j`/`k` and press `Enter` to jump |
| `o` | **Open Fuzzy File Picker**: Select `.md` or `.html` files in current directory tree |
| `v` | **Edit in External Editor (Vim / $EDITOR)**: Automatically pauses TUI and reloads upon exit |
| `t` | **Switch Color Theme**: Cycle through dark, light, tokyo-night, monokai, solarized, etc. |
| `/` | **Open Search Bar**: Type `/query` and press `Enter` to search |
| `n` | **Jump to Next Search Match** |
| `N` | **Jump to Previous Search Match** |
| `j` / `Page Up` | **Scroll Page Up** |
| `k` / `Page Down` | **Scroll Page Down** |
| `gg` / `Home` | **Jump to Top of document** |
| `G` / `End` | **Jump to Bottom of document** |
| `Down` / `Up` | Vertical scroll line by line |
| `Left` / `Right` | Horizontal scroll for wide content/code blocks |
| `Mouse Drag` | **Select Text**: Automatically copies selection to system clipboard on release |
| `Shift + Drag` | **Terminal Bypass Selection**: Force native terminal text selection |
| `m` | **Toggle Mouse Mode**: Switch between TUI mouse capture and native terminal selection mode |
| `Right Click` | **Context Menu**: Open floating modal for Copy / Search / Select All |
| `y` / `c` / `Ctrl+C` | **Manually copy current selection to clipboard** |
| `-` | **Narrow reading column width** (minimum 40 columns) |
| `=` / `+` | **Widen reading column width** (up to 100% full width) |
| `Cmd +` / `Cmd -` | **Terminal Font Zoom** (handled natively by terminal emulator) |
| `Mouse Wheel` | Scroll content |

---

## 📚 Documentation

- [User Manual (English)](docs/user_manual.md) | [使用者手冊 (繁體中文)](docs/user_manual_zh-TW.md)
- [Deployment & Installation Guide (English)](docs/deployment_guide.md) | [部署安裝指南 (繁體中文)](docs/deployment_guide_zh-TW.md)
- [Implementation Plan (English)](docs/implementation_plan.md) | [實作規劃書 (繁體中文)](docs/implementation_plan_zh-TW.md)

---

## 📄 License

This project is open-sourced under the [MIT License](LICENSE).
