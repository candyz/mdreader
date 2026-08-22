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
