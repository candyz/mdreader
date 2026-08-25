"""User configuration persistence module."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "mdreader"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict[str, Any]:
    """Load configuration from ~/.config/mdreader/config.json."""
    if not CONFIG_FILE.is_file():
        return {}
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_config(config: dict[str, Any]) -> None:
    """Save configuration dictionary to ~/.config/mdreader/config.json."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a single configuration value."""
    cfg = load_config()
    return cfg.get(key, default)


def set_config_value(key: str, value: Any) -> None:
    """Update and persist a single configuration value."""
    cfg = load_config()
    cfg[key] = value
    save_config(cfg)


def get_recent_files() -> list[str]:
    """Get list of recently opened file paths (up to 30)."""
    recents = get_config_value("recent_files", [])
    if not isinstance(recents, list):
        return []
    # Filter out non-existent files
    valid_recents = [f for f in recents if isinstance(f, str) and Path(f).exists()]
    return valid_recents[:30]


def add_recent_file(filepath: Path | str | None) -> None:
    """Add a file path to the recent files list and persist."""
    if not filepath:
        return
    try:
        p = Path(filepath).resolve()
        if not p.is_file():
            return
        p_str = str(p)
        recents = [f for f in get_recent_files() if f != p_str]
        recents.insert(0, p_str)
        set_config_value("recent_files", recents[:30])
    except Exception:
        pass


DEFAULT_KEYBINDINGS: dict[str, list[str]] = {
    "open_file_picker": ["o"],
    "toggle_toc": ["ctrl+o"],
    "open_commander": ["O"],
    "toggle_wrap": ["w"],
    "edit_in_editor": ["v", "f4"],
    "toggle_theme": ["t"],
    "quit": ["q"],
    "open_help": ["h", "?", "f1"],
    "handle_escape": ["escape"],
    "open_search": ["/"],
    "open_goto_line": [":"],
    "open_link": ["gx"],
    "list_marks": ["ctrl+m"],
    "toggle_mouse_mode": ["m"],
    "toggle_cmd_prompt": ["T"],
    "copy_selected_text": ["y", "c", "ctrl+c", "ctrl+y"],
    "search_next": ["n"],
    "search_prev": ["N"],
    "page_up": ["pageup", "u"],
    "page_down": ["pagedown", "i"],
    "scroll_up": ["up", "j"],
    "scroll_down": ["down", "k"],
    "scroll_left": ["left", "d"],
    "scroll_right": ["right", "f"],
    "zoom_out": ["-"],
    "zoom_in": ["=", "+"],
    "reset_zoom": ["0"],
    "export_document": ["e"],
    "copy_code_block": ["Y", "ctrl+k"],
    "open_in_terminal": ["ctrl+t"],
    "reveal_in_finder": ["ctrl+shift+o"],
    "toggle_line_numbers": ["l"],
    "scroll_end": ["G"],
    "reload_file": ["r"],
}

ACTION_DESCRIPTIONS: dict[str, tuple[str, bool]] = {
    "open_file_picker": ("Open", True),
    "toggle_toc": ("Outline", True),
    "open_commander": ("Commander", True),
    "toggle_wrap": ("Wrap", True),
    "edit_in_editor": ("Edit", True),
    "toggle_theme": ("Theme", True),
    "quit": ("Quit", True),
    "open_help": ("Help", True),
    "handle_escape": ("Cancel/Back", False),
    "open_search": ("Search (/)", False),
    "open_goto_line": ("Go to Line (:)", False),
    "open_link": ("Open Link (gx)", False),
    "list_marks": ("Marks (Ctrl+M)", False),
    "toggle_mouse_mode": ("Mouse Mode", False),
    "toggle_cmd_prompt": ("Terminal Prompt", False),
    "copy_selected_text": ("Copy", False),
    "search_next": ("Next match", False),
    "search_prev": ("Prev match", False),
    "page_up": ("Page Up", False),
    "page_down": ("Page Down", False),
    "scroll_up": ("Up", False),
    "scroll_down": ("Down", False),
    "scroll_left": ("Scroll Left", False),
    "scroll_right": ("Scroll Right", False),
    "zoom_out": ("Zoom Out (-)", False),
    "zoom_in": ("Zoom In (+)", False),
    "reset_zoom": ("Reset Zoom (0)", False),
    "export_document": ("Export (e)", False),
    "copy_code_block": ("Copy Code (Y)", False),
    "open_in_terminal": ("Terminal (Ctrl+T)", False),
    "reveal_in_finder": ("Reveal File", False),
    "toggle_line_numbers": ("Line No (L)", False),
    "scroll_end": ("Scroll End (Bottom)", False),
    "reload_file": ("Reload", False),
}


def get_keybindings() -> dict[str, list[str]]:
    """Get active keybindings merged from default and ~/.config/mdreader/config.json."""
    cfg = load_config()
    custom_bindings = cfg.get("keybindings", {})
    if not isinstance(custom_bindings, dict):
        custom_bindings = {}

    merged: dict[str, list[str]] = {}
    for action, default_keys in DEFAULT_KEYBINDINGS.items():
        if action in custom_bindings:
            custom_val = custom_bindings[action]
            if isinstance(custom_val, str):
                merged[action] = [custom_val]
            elif isinstance(custom_val, list):
                merged[action] = [str(k) for k in custom_val if isinstance(k, (str, int))]
            else:
                merged[action] = list(default_keys)
        else:
            merged[action] = list(default_keys)

    return merged


def normalize_key_for_textual(key: str) -> list[str]:
    """Convert user-friendly key strings into Textual key identifiers."""
    k = str(key).strip()
    k_lower = k.lower()
    if k_lower in ("?", "question_mark"):
        return ["question_mark"]
    elif k_lower in ("=", "equals", "equal", "equals_sign"):
        return ["equals_sign", "equals", "equal"]
    elif k_lower in ("+", "plus"):
        return ["plus"]
    elif k_lower in ("-", "minus"):
        return ["minus"]
    elif k_lower in ("/", "slash"):
        return ["slash"]
    elif k_lower in (":", "colon"):
        return ["colon"]
    elif k_lower in ("0", "zero"):
        return ["0", "zero"]
    elif k_lower in ("esc", "escape"):
        return ["escape"]
    elif k_lower in ("enter", "return"):
        return ["enter"]
    elif k_lower in ("space", " "):
        return ["space"]
    elif k_lower in ("tab", "\t"):
        return ["tab"]
    else:
        return [k]


def format_keybinding_display(keys: list[str]) -> str:
    """Format key list into friendly human-readable display string."""
    formatted: list[str] = []
    for k in keys:
        k_str = str(k).strip()
        if k_str == "question_mark":
            formatted.append("?")
        elif k_str in ("equals", "equal", "equals_sign"):
            formatted.append("=")
        elif k_str == "plus":
            formatted.append("+")
        elif k_str == "minus":
            formatted.append("-")
        elif k_str == "slash":
            formatted.append("/")
        elif k_str == "colon":
            formatted.append(":")
        elif k_str == "zero":
            formatted.append("0")
        elif k_str == "escape":
            formatted.append("Esc")
        elif k_str.lower() == "ctrl+shift+o":
            formatted.append("Ctrl+Shift+O")
        elif k_str.lower().startswith("ctrl+"):
            formatted.append(f"Ctrl+{k_str[5:].upper()}")
        elif k_str.lower().startswith("alt+"):
            formatted.append(f"Alt+{k_str[4:].upper()}")
        else:
            formatted.append(k_str)
    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for f in formatted:
        if f not in seen:
            seen.add(f)
            deduped.append(f)
    return " / ".join(deduped)


def build_app_bindings():
    """Generate Textual Binding objects dynamically from user configuration."""
    from textual.binding import Binding

    bindings_dict = get_keybindings()
    bindings_list: list[Binding] = []

    for action, keys in bindings_dict.items():
        desc, show = ACTION_DESCRIPTIONS.get(action, (action, False))
        is_first = True
        for key in keys:
            norm_keys = normalize_key_for_textual(key)
            for nk in norm_keys:
                show_binding = show if is_first else False
                bindings_list.append(Binding(nk, action, desc, show=show_binding))
                is_first = False

    return bindings_list
