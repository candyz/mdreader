"""High-performance directory content grep search with ripgrep (rg) acceleration and pure Python fallback."""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "build",
    "dist",
    ".pytest_cache",
    ".mypy_cache",
    "target",
}


def grep_search(
    root: Path | str,
    query: str,
    max_results: int = 100,
    case_sensitive: bool = False,
) -> List[Tuple[Path, int, str]]:
    """Search for query string in all text files under root directory.
    
    Returns a list of (filepath, line_number, line_text) tuples.
    """
    root_path = Path(root).resolve()
    if not root_path.is_dir() or not query.strip():
        return []

    # 1. Fast path: use ripgrep (rg) if installed
    rg_path = shutil.which("rg")
    if rg_path:
        try:
            cmd = [
                rg_path,
                "-n",
                "--no-heading",
                "--max-count", str(max_results),
                "--max-filesize", "5M",
            ]
            if not case_sensitive:
                cmd.append("-i")
            for exc in EXCLUDED_DIRS:
                cmd.extend(["-g", f"!{exc}"])
            cmd.extend([query, str(root_path)])

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5.0)
            matches: List[Tuple[Path, int, str]] = []
            for line in proc.stdout.splitlines():
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    try:
                        p = Path(parts[0])
                        lno = int(parts[1])
                        text = parts[2].strip()
                        matches.append((p, lno, text))
                        if len(matches) >= max_results:
                            break
                    except ValueError:
                        continue
            if matches:
                return matches
        except Exception:
            pass

    # 2. Fallback: pure Python scanner
    query_target = query if case_sensitive else query.lower()
    results: List[Tuple[Path, int, str]] = []

    for p in root_path.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in p.parts):
            continue
        if not p.is_file():
            continue
        try:
            st = p.stat()
            if st.st_size > 5 * 1024 * 1024 or st.st_size == 0:
                continue
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                for line_idx, line in enumerate(f):
                    check_line = line if case_sensitive else line.lower()
                    if query_target in check_line:
                        results.append((p, line_idx + 1, line.strip()))
                        if len(results) >= max_results:
                            return results
        except Exception:
            continue

    return results
