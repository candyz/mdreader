# mdreader — Terminal Markdown Reader

An interactive terminal Markdown previewer with native **Mermaid flowchart rendering** support (GUI-like experience in CLI), inspired by [leaf](https://github.com/RivoLink/leaf).

## Features

- 📑 **Rich Markdown Rendering**: Headers, tables, lists, quotes, styled code blocks.
- 📊 **Mermaid Flowchart Support**: Automatically renders ```` ```mermaid ```` diagrams as ASCII/Unicode art inline without crashing.
- 📑 **Interactive Table of Contents (TOC)**: Automatically extracts document headings into a clickable / keyboard-navigable sidebar (`Tab` to toggle).
- 🔄 **Watch Mode**: Live hot-reloading on disk changes (`-w` / `--watch`).
- 🎨 **Multi-Theme Support**: Built-in dark/light/retro color themes (`t` to switch in-app or `-t` flag).
- 🔍 **In-document Search Bar**: Quick search overlay triggered with `/`.
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
# Preview a markdown file interactively (with TOC sidebar)
mdreader README.md

# Preview test.md containing complex Mermaid flowchart
mdreader test.md

# Watch mode: auto-reload when file changes
mdreader -w test.md

# Set specific theme on launch
mdreader -t solarized-dark test.md

# Hide TOC sidebar on startup
mdreader --no-toc test.md

# Set maximum width (columns)
mdreader --width 100 test.md

# Non-interactive stdout preview
mdreader --inline test.md

# Stream or pipe from stdin
cat test.md | mdreader
```

## Keybindings (TUI Mode)

| Key | Action |
| :--- | :--- |
| `q` / `Esc` | Quit viewer / Dismiss search |
| `Tab` | Toggle Table of Contents (TOC) sidebar |
| `t` | Switch Color Theme (Dark, Light, Tokyo Night, Monokai, Solarized, Nord, etc.) |
| `/` | Open Search bar |
| `j` / `Down` | Scroll down |
| `k` / `Up` | Scroll up |
| `Page Up` / `Page Down` | Page scrolling |
| `Mouse wheel` | Scroll |
