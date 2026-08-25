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
| **`u`** / **`Page Up`** | **Page Up** (scroll one page up) |
| **`i`** / **`Page Down`** | **Page Down** (scroll one page down) |
| **`gg`** / **`Home`** | **Jump to Top of document** |
| **`G`** / **`End`** | **Jump to Bottom of document** |
| **`↑`** / **`j`** | Scroll line up |
| **`↓`** / **`k`** | Scroll line down |
| **`←`** / **`→`** / **`d`** / **`f`** | **Horizontal scroll** (`d`: left, `f`: right, useful for wide tables, code blocks, and charts) |
| **`/`** | **Open In-document Search**: Type `/keyword` and press `Enter` to start searching |
| **`n`** | **Jump to Next Search Match** |
| **`N`** | **Jump to Previous Search Match** |
| **`Mouse Drag`** | **Select Text**: Automatically copies selection to system clipboard on mouse release |
| **`Shift + Drag`** | **Terminal Bypass Selection**: Forces native terminal emulator text selection |
| **`m`** | **Toggle Mouse Mode**: One-key switch to disable TUI mouse tracking and restore native terminal mouse behavior |
| **`Right Click`** | **Context Menu**: Pop up floating context modal to select Copy / Search / Select All |
| **`y`** / **`c`** / **`Ctrl+C`** | **Copy Selection**: Manually copy selected text to system clipboard |
| **`-`** | **Narrow Column Width / Zoom Out** (-10 columns per press, minimum 40 columns) |
| **`=`** / **`+`** | **Widen Column Width / Zoom In** (+10 columns per press, up to 100% full width) |
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
mdreader -t vim-dark README.md
mdreader -t tokyo-night README.md
mdreader -t solarized-dark README.md
```
> Supported themes: `vim-dark`, `github-dark`, `github-light`, `textual-dark`, `textual-light`, `tokyo-night`, `monokai`, `solarized-dark`, `solarized-light`, `catppuccin-frappe`, `catppuccin-latte`, `dracula`, `nord`.

### 2. Restrict Maximum Reading Width (`--width`)
On ultra-wide or high-resolution monitors, restrict the text column width to enhance readability:
```bash
mdreader --width 100 README.md
```

### 3. File Watcher Mode (`-w` / `--watch`)
Auto-detect modifications on disk and perform instant live reloads:
```bash
mdreader -w notes.md
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

## ⚙️ Custom Keybindings (`~/.config/mdreader/config.json`)

`mdreader` allows complete customization of all keyboard shortcuts through `~/.config/mdreader/config.json`.

### 1. Configuration Example

```json
{
  "theme": "vim-dark",
  "keybindings": {
    "quit": ["q", "escape"],
    "open_file_picker": "o",
    "toggle_toc": "ctrl+o",
    "open_commander": "O",
    "toggle_wrap": "w",
    "edit_in_editor": ["v", "f4"],
    "toggle_theme": "t",
    "open_help": ["h", "?", "f1"],
    "open_search": "/",
    "open_goto_line": ":",
    "page_down": ["pagedown", "i"],
    "page_up": ["pageup", "u"],
    "scroll_down": ["down", "k"],
    "scroll_up": ["up", "j"],
    "zoom_in": ["=", "+"],
    "zoom_out": "-",
    "toggle_line_numbers": "l",
    "reset_zoom": "0"
  }
}
```

### 2. Common Keymap Presets

#### 🅰️ Vim-centric Preset
```json
{
  "keybindings": {
    "page_down": ["ctrl+f", "ctrl+d", "pagedown", "i"],
    "page_up": ["ctrl+b", "ctrl+u", "pageup", "u"],
    "scroll_down": ["j", "down", "k"],
    "scroll_up": ["k", "up", "j"],
    "scroll_left": ["h", "left"],
    "scroll_right": ["l", "right"],
    "scroll_end": "G",
    "open_search": "/",
    "open_goto_line": ":"
  }
}
```

#### 🅱️ Emacs-centric Preset
```json
{
  "keybindings": {
    "page_down": ["ctrl+v", "pagedown"],
    "page_up": ["alt+v", "pageup"],
    "scroll_down": ["ctrl+n", "down"],
    "scroll_up": ["ctrl+p", "up"],
    "scroll_left": ["ctrl+b", "left"],
    "scroll_right": ["ctrl+f", "right"],
    "open_file_picker": "ctrl+x ctrl+f",
    "quit": ["ctrl+x ctrl+c", "q"]
  }
}
```

### 3. Configurable Action Reference

| Action Identifier | Default Key(s) | Description |
| :--- | :--- | :--- |
| `quit` | `q` | Exit application |
| `open_file_picker` | `o` | Open fuzzy file picker |
| `toggle_toc` | `ctrl+o` | Table of contents outline |
| `open_commander` | `O` | Midnight Commander dual-pane manager |
| `toggle_wrap` | `w` | Toggle soft line wrap |
| `edit_in_editor` | `v`, `f4` | Edit in external editor / viewer |
| `toggle_theme` | `t` | Cycle color themes |
| `open_help` | `h`, `?`, `f1` | Open help shortcuts dialog |
| `handle_escape` | `escape` | Cancel / Dismiss modal |
| `open_search` | `/` | In-document search |
| `open_goto_line` | `:` | Jump to line number |
| `search_next` | `n` | Next search match |
| `search_prev` | `N` | Previous search match |
| `page_up` | `pageup`, `u` | Scroll page up |
| `page_down` | `pagedown`, `i` | Scroll page down |
| `scroll_up` | `up`, `j` | Scroll line up |
| `scroll_down` | `down`, `k` | Scroll line down |
| `scroll_left` | `left`, `d` | Scroll left (image / nowrap) |
| `scroll_right` | `right`, `f` | Scroll right (image / nowrap) |
| `scroll_end` | `G` | Jump to bottom of document |
| `zoom_in` | `=`, `+` | Zoom in reading width / image |
| `zoom_out` | `-` | Zoom out reading width / image |
| `reset_zoom` | `0` | Reset zoom to 100% |
| `export_document` | `e` | Export document (HTML / Text / MD) |
| `copy_code_block` | `Y`, `ctrl+k` | Extract and copy code blocks |
| `copy_selected_text`| `y`, `c`, `ctrl+c`, `ctrl+y` | Copy selection or full text |
| `toggle_mouse_mode` | `m` | Toggle mouse selection mode |
| `toggle_cmd_prompt` | `T` | Toggle terminal prompt bar |
| `open_in_terminal` | `ctrl+t` | Open terminal shell in file dir |
| `reveal_in_finder` | `ctrl+shift+o` | Reveal in Finder / file manager |
| `toggle_line_numbers`| `l` | Toggle line number column |
| `reload_file` | `r` | Reload file from disk |

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
