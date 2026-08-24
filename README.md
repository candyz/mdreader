# mdreader — Terminal Markdown Reader

[繁體中文版 (Traditional Chinese)](README_zh-TW.md)

An interactive terminal Markdown and HTML previewer with native **Mermaid flowchart rendering** support (GUI-like experience in CLI), inspired by [leaf](https://github.com/RivoLink/leaf).

---

## ✨ Features

- 📑 **Rich Markdown & Mermaid Flowcharts**: Headers, tables, lists, blockquotes, syntax-highlighted code blocks, and native ```` ```mermaid ```` ASCII/Unicode flowchart rendering.
- ⚡ **Gigabyte-level Extreme Large File Performance**: Built-in zero-copy `mmap` lazy line buffer and uint line indexing. Opens 100,000+ line files in 30ms with < 10MB constant RAM and sub-millisecond byte searching.
- 💻 **Vim-like Navigation & Line Jumping**:
  - Soft wrap toggle (`w` / `Alt+Z`)
  - Jump to line with `:` prompt or numeric buffer (`:123`, `500G`, `42gg`)
  - Vim marks and bookmarks (`m` + key to mark, `'` + key to jump, `Ctrl+M` to browse)
  - Hyperlink extractor & browser opener (`gx`)
- 📊 **Responsive Enhanced Status Bar**:
  - Real-time indicator: `1.5M │ Markdown │ [WRAP] │ Ln 42/1000 (4%)`
  - Responsive hierarchical hiding on narrow screens (< 95 columns).
- 📁 **Midnight Commander Dual-Pane File Manager (`Ctrl+O`)**:
  - `Tab` switch active pane, `Insert`/`Space` multi-selection, `F3` view, `F4` edit, `F5` copy, `F6` move/rename, `F7` mkdir, `F8` delete, `s` / `F2` sorting (Name/Size/Time/Ext), `Ctrl+D` directory bookmarks, `Ctrl+F` folder grep search.
- 🔍 **Folder Content Grep Search (`Ctrl+F`)**:
  - Blazing-fast full-text search across directory trees with `ripgrep (rg)` acceleration and pure Python streaming fallback. Jumps directly to matching file line.
- 🔖 **Directory Bookmarks & Quick Jump (`Ctrl+D`)**:
  - Jump instantly to Home (`~`), Workspace Root, Downloads, Desktop, Documents, Root (`/`), or recent directories.
- 📂 **Fzf-style Fuzzy File Picker (`o`)**:
  - Subsequence match scoring, Recent Files toggle (`Ctrl+R`), Hidden Dotfiles toggle (`Ctrl+H` / `Ctrl+A`), and directory remembrance.
- 📤 **Standalone HTML & Text Export (`e` / CLI `--export-html`)**:
  - Export beautiful standalone HTML documents with modern dark/light CSS or plain text.
- 💻 **Code Block Extraction (`Y` / `Ctrl+K`)**:
  - Extract and copy code blocks directly to clipboard.
- 🛠️ **System Tool Integration**:
  - `v` / `F4`: Edit with `$EDITOR` / `vim` and auto hot-reload
  - `Ctrl+T`: Open terminal shell in current file directory
  - `Ctrl+Shift+O`: Reveal file in macOS Finder or Linux file manager
- 🔄 **Watch Mode**: Live hot-reloading on disk changes (`-w` / `--watch`).
- 🎨 **Multi-Theme Support**: Built-in 10+ themes (`t` to cycle, `--list-themes`), persisted across sessions.
- 🖱️ **Mouse Selection & System Clipboard**: Seamless clipboard integration (macOS `pbcopy`, Linux Wayland `wl-copy`, X11 `xclip`, OSC 52). Toggle mouse mode with `m`.
- 📟 **CLI Automation**: Line jumping (`+50` / `-l 50`), headless export (`--export-html`), and stdout pipe (`--inline`).

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
# 1. Open interactive file picker
mdreader

# 2. Open specific file and jump to line 50
mdreader +50 README.md
mdreader -l 50 README.md

# 3. Preview HTML document or massive log file
mdreader index.html
mdreader gigantic_data.log

# 4. Watch mode: auto-reload on file changes
mdreader -w README.md

# 5. List available themes and select theme on launch
mdreader --list-themes
mdreader -t tokyo-night README.md

# 6. Headless export to standalone HTML or Plain Text (no GUI)
mdreader README.md --export-html /tmp/readme.html
mdreader README.md --export-txt /tmp/readme.txt

# 7. Non-interactive stdout preview (ideal for fzf previewer)
mdreader --inline README.md

# 8. Stream or pipe from stdin
cat test.md | mdreader
curl -s https://example.com | mdreader

# 9. Specify syntax highlighting override (e.g. sh, python, json)
mdreader -s python snippet.dat
mdreader -s sh config.env
```

---

## ⌨️ Keybindings (TUI Mode)

| Key | Action |
| :--- | :--- |
| `q` / `Esc` | Quit viewer / Dismiss modal or search |
| `h` / `?` / `F1` | **Help**: Open comprehensive keyboard shortcuts & feature guide dialog |
| `o` | **Open Fuzzy File Picker**: Browse files, `Ctrl+R` recent, `Ctrl+D` bookmarks, `Ctrl+F` grep |
| `O` | **Table of Contents (Outline)**: Navigate headings and press `Enter` to jump |
| `Ctrl+O` | **Midnight Commander Mode**: Dual-pane file manager (`Tab` switch pane, `Ins`/`Space` multi-select, `F3` view, `F4` edit, `F5` copy, `F6` ren/mov, `F7` mkdir, `F8` delete, `s` sort, `Ctrl+D` bookmarks, `Ctrl+F` grep) |
| `w` / `Alt+Z` | **Toggle Soft Line Wrap**: Switch between automatic line wrapping and horizontal scrolling |
| `L` / `Alt+L` | **Toggle Line Numbers**: Show/hide line numbers column in code & plain text files |
| `gx` | **Extract & Open Hyperlinks**: Extract web links and open in default browser |
| `m` + `[a-z]` | **Set Bookmark (Mark)**: Set bookmark at current line |
| `'` + `[a-z]` | **Jump to Bookmark**: Jump to previously saved bookmark line |
| `Ctrl+M` | **List Bookmarks**: Open modal to view and select all bookmarks |
| `:` / `[N]G` / `[N]gg` | **Go to Line**: Jump to line number |
| `e` | **Export Document**: Export to Standalone HTML, Plain Text, or Markdown |
| `Y` / `Ctrl+K` | **Copy Code Block**: Extract and copy code blocks to clipboard |
| `v` | **Edit in External Editor (Vim / $EDITOR)**: Pauses TUI and reloads upon exit |
| `Ctrl+T` | **Open Full Terminal Shell**: Launch interactive `$SHELL` in file directory |
| `T` | **Toggle Terminal Prompt Bar**: Midnight Commander style inline shell prompt above status bar |
| `Ctrl+Shift+O` | **Reveal File**: Reveal in macOS Finder or Linux file manager |
| `t` | **Switch Color Theme**: Cycle through built-in color themes |
| `/` | **Search**: Vim-style search overlay (`n` next, `N` prev) |
| `j` / `Page Up` | Scroll page up |
| `k` / `Page Down` | Scroll page down |
| `gg` / `Home` | Jump to top of document |
| `G` / `End` | Jump to bottom of document |
| `y` / `c` / `Ctrl+C` | Copy mouse selection or entire document to system clipboard |
| `m` | **Toggle Mouse Mode**: Switch between TUI mouse capture and native terminal selection |
| `-` / `=` | Adjust reading column width |
| `+` / `=` / `z` | **Zoom In Image**: Increase image display scale (+20%) |
| `-` / `Z` | **Zoom Out Image**: Decrease image display scale (-20%) |
| `0` | **Reset Image Zoom**: Reset image display scale to 100% |
| `↑` / `↓` / `←` / `→` / `jkdf` | **Pan Image**: Scroll and pan image across viewport |

---

## ⚙️ Custom Keybindings (`~/.config/mdreader/config.json`)

You can customize any keybinding by adding a `"keybindings"` section in `~/.config/mdreader/config.json`. Each action accepts a single key string or an array of key aliases:

```json
{
  "theme": "github-dark",
  "keybindings": {
    "quit": ["q", "escape"],
    "open_file_picker": "o",
    "toggle_toc": "O",
    "open_commander": "ctrl+o",
    "toggle_wrap": ["w", "alt+z"],
    "edit_in_editor": ["v", "f4"],
    "toggle_theme": "t",
    "open_help": ["h", "?", "f1"],
    "open_search": "/",
    "open_goto_line": ":",
    "page_down": ["pagedown", "d", "ctrl+f"],
    "page_up": ["pageup", "u", "ctrl+b"],
    "scroll_down": ["down", "j"],
    "scroll_up": ["up", "k"],
    "zoom_in": ["+", "=", "z"],
    "zoom_out": ["-", "Z"],
    "reset_zoom": "0"
  }
}
```

### Configurable Action Identifiers

| Action Name | Default Key(s) | Description |
| :--- | :--- | :--- |
| `quit` | `q` | Quit viewer / Exit app |
| `open_file_picker` | `o` | Open interactive fuzzy file picker |
| `toggle_toc` | `O` | Open table of contents outline |
| `open_commander` | `ctrl+o` | Open Midnight Commander dual-pane manager |
| `toggle_wrap` | `w`, `alt+z` | Toggle soft line wrap |
| `edit_in_editor` | `v`, `f4` | Edit in external editor / viewer |
| `toggle_theme` | `t` | Cycle color theme |
| `open_help` | `h`, `?`, `f1` | Open help shortcut dialog |
| `handle_escape` | `escape` | Cancel / Dismiss modal |
| `open_search` | `/` | In-document search |
| `open_goto_line` | `:` | Jump to line number |
| `search_next` | `n` | Next search match |
| `search_prev` | `N` | Previous search match |
| `page_up` | `j` | Scroll page up |
| `page_down` | `k` | Scroll page down |
| `scroll_up` | `up` | Scroll line up |
| `scroll_down` | `down` | Scroll line down |
| `scroll_left` | `left`, `d` | Scroll left (image / nowrap) |
| `scroll_right` | `right`, `f` | Scroll right (image / nowrap) |
| `scroll_end` | `G` | Jump to bottom of document |
| `zoom_in` | `=`, `+`, `z` | Zoom in reading width / image |
| `zoom_out` | `-`, `Z` | Zoom out reading width / image |
| `reset_zoom` | `0` | Reset zoom to 100% |
| `export_document` | `e` | Export document (HTML / Text / MD) |
| `copy_code_block` | `Y`, `ctrl+k` | Extract and copy code blocks |
| `copy_selected_text`| `y`, `c`, `ctrl+c`, `ctrl+y` | Copy selection or full text |
| `toggle_mouse_mode` | `m` | Toggle mouse selection mode |
| `toggle_cmd_prompt` | `T` | Toggle terminal prompt bar |
| `open_in_terminal` | `ctrl+t` | Open terminal shell in file dir |
| `reveal_in_finder` | `ctrl+shift+o` | Reveal in Finder / file manager |
| `toggle_line_numbers`| `L`, `alt+l` | Toggle line number column |
| `reload_file` | `r` | Reload file from disk |

---

## 📚 Documentation

- [User Manual (English)](docs/user_manual.md) | [使用者手冊 (繁體中文)](docs/user_manual_zh-TW.md)
- [Deployment & Installation Guide (English)](docs/deployment_guide.md) | [部署安裝指南 (繁體中文)](docs/deployment_guide_zh-TW.md)
- [Implementation Plan (English)](docs/implementation_plan.md) | [實作規劃書 (繁體中文)](docs/implementation_plan_zh-TW.md)

---

## 📄 License

This project is open-sourced under the [MIT License](LICENSE).
