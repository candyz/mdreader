# mdreader — Terminal Markdown Reader

An interactive terminal Markdown previewer with native **Mermaid flowchart rendering** support (GUI-like experience in CLI), inspired by [leaf](https://github.com/RivoLink/leaf).

## Features

- 📑 **Rich Markdown Rendering**: Headers, tables, lists, quotes, styled code blocks.
- 📊 **Mermaid Flowchart Support**: Automatically renders ```` ```mermaid ```` diagrams as ASCII/Unicode art inline without crashing.
- ⚡ **Interactive TUI**: Smooth scrolling, custom width, vim keybindings (`j`/`k`/`q`/`Esc`).
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
# Preview a markdown file interactively
mdreader README.md

# Preview test.md containing complex Mermaid flowchart
mdreader test.md

# Set maximum width (columns)
mdreader --width 100 test.md

# Non-interactive stdout preview
mdreader --inline test.md

# Stream or pipe from stdin
cat test.md | mdreader
```

## Keybindings (TUI Mode)

- `q` / `Esc`: Quit viewer
- `j` / `Down`: Scroll down
- `k` / `Up`: Scroll up
- `Page Up` / `Page Down`: Page scrolling
- `Mouse wheel`: Scroll
