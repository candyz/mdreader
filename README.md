# mdreader — Terminal Markdown Reader

An interactive terminal Markdown previewer with native **Mermaid flowchart rendering** support (GUI-like experience in CLI), inspired by [leaf](https://github.com/RivoLink/leaf).

## Features

- 📑 **Rich Markdown Rendering**: Headers, tables, lists, quotes, styled code blocks.
- 📊 **Mermaid Flowchart Support**: Automatically renders ```` ```mermaid ```` diagrams as ASCII/Unicode art inline without crashing.
- 📑 **Interactive Table of Contents (TOC)**: Automatically extracts document headings into a clickable / keyboard-navigable sidebar (`Tab` to toggle).
- 📂 **Fuzzy File Picker**: Interactive modal file selector with instant filtering (`o` key in TUI or launch `mdreader` without arguments).
- 🔄 **Watch Mode**: Live hot-reloading on disk changes (`-w` / `--watch`).
- 🎨 **Multi-Theme Support**: Built-in dark/light/retro color themes (`t` to switch in-app or `-t` flag).
- 🔍 **In-document Search Bar**: Quick search overlay triggered with `/`.
- 🖼️ **Terminal Graphics Protocol Ready**: iTerm2 / Kitty inline image protocol integration.
- ⚡ **Interactive TUI**: Smooth scrolling, custom width (`--width`), vim keybindings (`j`/`k`/`q`/`Esc`).
- 📟 **Inline Mode**: Pipe directly to terminal with ANSI colors via `--inline`.
- 🔌 **Stdin Pipe**: Supports piping directly from CLI tools (e.g. `cat file.md | mdreader` or AI tools).

## Installation

```bash
# Clone the repository
git clone https://github.com/candyz0416/mdreader.git
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

# 2. Preview a specific markdown file interactively (with TOC sidebar)
mdreader README.md

# 3. Preview test.md containing complex Mermaid flowchart
mdreader test.md

# 4. Watch mode: auto-reload when file changes
mdreader -w test.md

# 5. Set specific theme on launch
mdreader -t solarized-dark test.md

# 6. Hide TOC sidebar on startup
mdreader --no-toc test.md

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
| `o` | Open Fuzzy File Picker modal |
| `Tab` | Toggle Table of Contents (TOC) sidebar |
| `t` | Switch Color Theme (Dark, Light, Tokyo Night, Monokai, Solarized, Nord, etc.) |
| `/` | Open Search bar |
| `j` / `Page Down` | Scroll Page Down (下一頁) |
| `k` / `Page Up` | Scroll Page Up (上一頁) |
| `Down` / `Up` | Line by line scroll (逐行捲動) |
| `Mouse wheel` | Scroll |
