# 📖 mdreader User Manual

[繁體中文版 (Traditional Chinese)](user_manual_zh-TW.md)

**mdreader** is an interactive Markdown and HTML reader engineered for Terminal and CLI developers. It features a clean, modernized full-screen TUI interface (maximizing viewport area with a real-time clock integrated into the bottom bar) and native **Mermaid flowchart to ASCII visualization rendering**, completely solving the crash issues that traditional tools (such as leaf) encounter with mermaid syntax.

---

## 🎯 Quick Start

### 1. Open Markdown or HTML Files
```bash
# Open Markdown document
mdreader README.md
mdreader docs/implementation_plan.md

# Open HTML web document (auto-converted while preserving outline & formatting)
mdreader index.html
mdreader docs/api_reference.html
```

### 2. Launch Without Arguments (Fuzzy File Picker)
When launched without arguments, `mdreader` automatically scans the current working directory and subdirectories for `.md` and `.html` files:
```bash
mdreader
```

### 3. Live Hot-Reload (Watch Mode)
When editing documents, web pages, or notes, enable watch mode to have the terminal viewport update automatically on every disk write:
```bash
mdreader -w README.md
mdreader --watch index.html
```

---

## ⌨️ Keyboard Navigation & Keybindings

Navigate effortlessly inside the interactive TUI with the following shortcuts:

| Shortcut | Description |
| :--- | :--- |
| **`q`** / **`Esc`** | Quit `mdreader` / Dismiss current modal or search input |
| **`O`** | **Open Outline Modal (TOC)**: Browse document headings, select with `↑`/`↓`/`j`/`k`, and press `Enter` to jump |
| **`o`** | **Open Fuzzy File Picker**, allowing quick switching between documents |
| **`Ctrl+O`** | **Midnight Commander Mode**: Dual-pane file manager (`Tab` switch pane, `Ins`/`Space` select, `F3` view, `F4` edit, `F5` copy, `F6` ren/mov, `F7` mkdir, `F8` delete, `Ctrl+O`/`Esc` return) |
| **`v`** | **Edit in External Editor (Vim / $EDITOR)**: Suspends TUI, opens editor, and auto-reloads upon saving & exiting |
| **`t`** | **Cycle Color Themes** (Dark, Light, Tokyo Night, Monokai, Solarized, Dracula, etc. - automatically remembered) |
| **`j`** / **`Page Up`** | **Page Up** (scroll one page up) |
| **`k`** / **`Page Down`** | **Page Down** (scroll one page down) |
| **`gg`** / **`Home`** | **Jump to Top of document** |
| **`G`** / **`End`** | **Jump to Bottom of document** |
| **`↓`** / **`↑`** | Smooth vertical scroll line-by-line |
| **`←`** / **`→`** / **`d`** / **`f`** | **Horizontal scroll** (`d`: left, `f`: right, useful for wide tables, code blocks, and charts) |
| **`/`** | **Open In-document Search**: Type `/keyword` and press `Enter` to start searching |
| **`n`** | **Jump to Next Search Match** |
| **`N`** | **Jump to Previous Search Match** |
| **`Mouse Drag`** | **Select Text**: Automatically copies selection to system clipboard on mouse release |
| **`Shift + Drag`** | **Terminal Bypass Selection**: Forces native terminal emulator text selection |
| **`m`** | **Toggle Mouse Mode**: One-key switch to disable TUI mouse tracking and restore native terminal mouse behavior |
| **`Right Click`** | **Context Menu**: Pop up floating context modal to select Copy / Search / Select All |
| **`y`** / **`c`** / **`Ctrl+C`** | **Copy Selection**: Manually copy selected text to system clipboard |
| **`-`** | **Narrow Column Width** (-10 columns per press, minimum 40 columns) |
| **`=`** / **`+`** | **Widen Column Width** (+10 columns per press, up to 100% full width) |
| **`Cmd +`** / **`Cmd -`** | **Terminal Font Zoom** (handled natively by your terminal emulator) |
| **Mouse Wheel** | Scroll content smoothly |

---

## 📝 External Editor Integration (Edit with Vim)

While browsing a document, press **`v`** at any time to open your preferred terminal editor:
- **Environment Variable Support**: Prioritizes `$EDITOR` or `$VISUAL` (defaults to `vim`, falling back to `vi` or `nano`).
- **Seamless Suspend & Resume**: `mdreader` automatically pauses the TUI, hands over terminal control to the editor, and upon exit (e.g., `:wq`), restores the TUI and **instantly reloads the updated content and re-renders Mermaid diagrams**.

---

## ⚙️ Advanced CLI Options & Use Cases

### 1. Specify Interface Color Theme (`-t` / `--theme`)
Specify color schemes directly from the command line:
```bash
mdreader -t tokyo-night README.md
mdreader -t solarized-dark README.md
mdreader -t textual-light README.md
```
> Supported themes: `textual-dark`, `textual-light`, `tokyo-night`, `monokai`, `solarized-dark`, `solarized-light`, `catppuccin-frappe`, `catppuccin-latte`, `dracula`, `nord`.

### 2. Restrict Maximum Reading Width (`--width`)
On ultra-wide or high-resolution monitors, restrict the text column width to enhance readability:
```bash
mdreader --width 100 README.md
```

### 3. Display TOC Sidebar on Startup (`--toc`)
By default, `mdreader` opens in full-page mode. Use `--toc` to open with the Table of Contents outline sidebar immediately visible:
```bash
mdreader --toc README.md
```

### 4. Non-Interactive Inline Mode (`--inline`)
Renders formatted ANSI color output directly to standard output without entering TUI mode (perfect for CLI scripts or `fzf` previews):
```bash
mdreader --inline README.md

# Pair with fzf for live document preview
fzf --preview 'mdreader --inline {}'
```

### 5. Standard Input Piping (Stdin)
Accept piped input directly from other command-line tools:
```bash
cat README.md | mdreader

# Pipe AI CLI or curl outputs
curl -s https://example.com | mdreader
echo -e "# Test Title\n\`\`\`mermaid\ngraph LR\nA --> B\n\`\`\`" | mdreader
```

---

## 📊 Mermaid Diagram Support

`mdreader` automatically parses ```` ```mermaid ```` code blocks in Markdown and converts them into ASCII/Unicode diagram trees:

- **Supported Diagram Types**: `graph TD` (flowcharts), `graph LR`, `flowchart`, `stateDiagram`, etc.
- **Fault-Tolerant Fallback**: If a diagram contains unsupported syntax, `mdreader` gracefully wraps the original code with a warning block without crashing.

---

## ❓ Troubleshooting

1. **Font & Character Alignment**:
   - Ensure your terminal uses a monospace font with Nerd Fonts or standard unicode box-drawing support (e.g., JetBrains Mono, FiraCode, or SF Mono).
2. **Terminal Colors**:
   - Ensure 24-bit True Color is enabled in your environment: `export COLORTERM=truecolor`.
3. **Linux / GNOME Terminal Clipboard Sync**:
   - Linux X11 and Wayland desktop environments rely on system clipboard utilities. If copying does not sync to external applications, install the required tool:
     - Ubuntu / Debian: `sudo apt install xclip wl-clipboard`
     - Arch / Manjaro: `sudo pacman -S xclip wl-clipboard`
     - Rocky Linux / RHEL: `sudo dnf install xclip wl-clipboard`
   - Linux provides two clipboard buffers:
     - **Mouse Middle-Click**: Pastes current selection (Primary selection).
     - **`Ctrl + Shift + V`** (Terminal) / **`Ctrl + V`** (Browser/App): Pastes standard Clipboard.
