"""Auto-updater for mdreader CLI tool."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from rich.console import Console

from mdreader import __version__

console = Console()

GITHUB_RAW_PYPROJECT_URL = "https://raw.githubusercontent.com/candyz/mdreader/main/pyproject.toml"
GITHUB_REPO_URL = "git+https://github.com/candyz/mdreader.git"


def parse_semver(version_str: str) -> Tuple[int, int, int]:
    """Parse a semantic version string (e.g. '1.5.1' or 'v1.6.0') into (major, minor, patch)."""
    cleaned = version_str.strip().lstrip("v")
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", cleaned)
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def is_newer_version(current_ver: str, remote_ver: str) -> bool:
    """Return True if remote_ver is strictly greater than current_ver."""
    return parse_semver(remote_ver) > parse_semver(current_ver)


@dataclass
class UpdateCheckResult:
    current_version: str
    latest_version: Optional[str]
    has_update: bool
    error: Optional[str] = None


def fetch_latest_version(timeout: float = 5.0) -> UpdateCheckResult:
    """Fetch latest version from GitHub raw pyproject.toml."""
    current_ver = __version__
    try:
        req = urllib.request.Request(
            GITHUB_RAW_PYPROJECT_URL,
            headers={"User-Agent": f"mdreader/{current_ver}"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                return UpdateCheckResult(
                    current_version=current_ver,
                    latest_version=None,
                    has_update=False,
                    error=f"HTTP {response.status} fetching remote version",
                )
            text = response.read().decode("utf-8")

        m = re.search(r'version\s*=\s*"([^"]+)"', text)
        if not m:
            return UpdateCheckResult(
                current_version=current_ver,
                latest_version=None,
                has_update=False,
                error="Could not parse version from remote pyproject.toml",
            )

        latest_ver = m.group(1).strip()
        has_update = is_newer_version(current_ver, latest_ver)
        return UpdateCheckResult(
            current_version=current_ver,
            latest_version=latest_ver,
            has_update=has_update,
        )
    except Exception as e:
        return UpdateCheckResult(
            current_version=current_ver,
            latest_version=None,
            has_update=False,
            error=str(e),
        )


def detect_install_method() -> str:
    """Detect how mdreader was installed (pipx, uv_tool, git_repo, pip)."""
    executable = sys.executable

    # 1. Check if running under pipx
    if "pipx/venvs/mdreader" in executable:
        return "pipx"

    # 2. Check if running inside uv tool
    if "uv/tools/mdreader" in executable or ".local/share/uv/tools/mdreader" in executable:
        receipt_path = Path.home() / ".local" / "share" / "uv" / "tools" / "mdreader" / "uv-receipt.toml"
        if receipt_path.is_file():
            try:
                txt = receipt_path.read_text(encoding="utf-8")
                if "directory =" in txt:
                    return "uv_tool_local"
            except Exception:
                pass
        return "uv_tool"

    # 3. Check if running in a local cloned repo directory
    try:
        root_dir = Path(__file__).resolve().parent.parent.parent
        if (root_dir / ".git").is_dir() and (root_dir / "pyproject.toml").is_file():
            return "git_repo"
    except Exception:
        pass

    # 4. Fallback: check if pipx or uv is available on the system
    if shutil.which("pipx"):
        return "pipx"
    if shutil.which("uv"):
        return "uv_tool"

    return "pip"


def perform_update(force: bool = False) -> bool:
    """Check for update and execute the upgrade command with user feedback."""
    console.print("[dim cyan]🔍 Checking for mdreader updates...[/dim cyan]")
    check = fetch_latest_version()

    if check.error:
        console.print(f"[bold red]❌ Failed to check for updates:[/bold red] {check.error}")
        return False

    current = check.current_version
    latest = check.latest_version or current

    if not check.has_update and not force:
        console.print(f"[bold green]✓ mdreader is already up to date[/bold green] (version [bold cyan]{current}[/bold cyan]).")
        return True

    if check.has_update:
        console.print(f"✨ [bold green]New version available:[/bold green] [bold cyan]{current}[/bold cyan] → [bold magenta]{latest}[/bold magenta]")
    else:
        console.print(f"[dim]Reinstalling/updating current version [bold cyan]{current}[/bold cyan] (force mode)...[/dim]")

    method = detect_install_method()
    console.print(f"[dim]Detected installation method: [bold]{method}[/bold][/dim]")

    try:
        with console.status(f"[dim cyan]Updating mdreader to v{latest}...[/dim cyan]", spinner="dots"):
            if method == "git_repo":
                root_dir = Path(__file__).resolve().parent.parent.parent
                # 1. git fetch & reset to origin/main
                res_fetch = subprocess.run(
                    ["git", "fetch", "origin", "main"],
                    cwd=str(root_dir),
                    capture_output=True,
                    text=True,
                )
                if res_fetch.returncode == 0:
                    subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=str(root_dir), capture_output=True)
                else:
                    # fallback to pull
                    subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=str(root_dir), capture_output=True)

                # 2. reinstall
                if shutil.which("pipx"):
                    cmd = ["pipx", "install", str(root_dir), "--force"]
                elif shutil.which("uv"):
                    cmd = ["uv", "tool", "install", "--force", "--reinstall", str(root_dir)]
                else:
                    cmd = [sys.executable, "-m", "pip", "install", "-e", str(root_dir)]

                res_inst = subprocess.run(cmd, cwd=str(root_dir), capture_output=True, text=True)
                if res_inst.returncode != 0:
                    console.print(f"[bold red]Reinstallation failed:[/bold red] {res_inst.stderr.strip()}")
                    return False

            elif method == "uv_tool_local":
                receipt_path = Path.home() / ".local" / "share" / "uv" / "tools" / "mdreader" / "uv-receipt.toml"
                local_dir = None
                try:
                    txt = receipt_path.read_text(encoding="utf-8")
                    m = re.search(r'directory\s*=\s*"([^"]+)"', txt)
                    if m:
                        local_dir = m.group(1)
                except Exception:
                    pass

                if local_dir and Path(local_dir).is_dir():
                    if (Path(local_dir) / ".git").is_dir():
                        rf = subprocess.run(["git", "fetch", "origin", "main"], cwd=local_dir, capture_output=True)
                        if rf.returncode == 0:
                            subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=local_dir, capture_output=True)
                        else:
                            subprocess.run(["git", "pull", "origin", "main"], cwd=local_dir, capture_output=True)
                    cmd = ["uv", "tool", "install", "--force", "--reinstall", local_dir]
                else:
                    cmd = ["uv", "tool", "install", "--force", "--reinstall", GITHUB_REPO_URL]

                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode != 0:
                    console.print(f"[bold red]uv tool update failed:[/bold red] {res.stderr.strip()}")
                    return False

            elif method == "uv_tool":
                cmd = ["uv", "tool", "install", "--force", "--reinstall", GITHUB_REPO_URL]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode != 0:
                    console.print(f"[bold red]uv tool update failed:[/bold red] {res.stderr.strip()}")
                    return False

            elif method == "pipx":
                # Check if local repo exists and is valid
                local_repo = Path.home() / "AI" / "agy" / "mdreader"
                if not local_repo.is_dir():
                    local_repo = Path.home() / "AI" / "mdreader"

                install_from_remote = True
                if local_repo.is_dir() and (local_repo / ".git").is_dir():
                    # Attempt git fetch & reset --hard origin/main to clean local working tree conflicts
                    rf = subprocess.run(["git", "fetch", "origin", "main"], cwd=str(local_repo), capture_output=True)
                    if rf.returncode == 0:
                        rr = subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=str(local_repo), capture_output=True)
                        if rr.returncode == 0:
                            install_from_remote = False

                if not install_from_remote:
                    # Try pip backend fallback for environments without uv
                    res = subprocess.run(["pipx", "install", str(local_repo), "--force", "--backend", "pip"], capture_output=True, text=True)
                    if res.returncode != 0:
                        res = subprocess.run(["pipx", "install", str(local_repo), "--force"], capture_output=True, text=True)
                else:
                    res = subprocess.run(["pipx", "install", GITHUB_REPO_URL, "--force", "--backend", "pip"], capture_output=True, text=True)
                    if res.returncode != 0:
                        res = subprocess.run(["pipx", "install", GITHUB_REPO_URL, "--force"], capture_output=True, text=True)

                if res.returncode != 0:
                    console.print(f"[bold red]pipx update failed:[/bold red] {res.stderr.strip()}")
                    return False

            else:
                # pip fallback
                cmd = [sys.executable, "-m", "pip", "install", "--upgrade", GITHUB_REPO_URL]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode != 0:
                    console.print(f"[bold red]pip update failed:[/bold red] {res.stderr.strip()}")
                    return False

        console.print(f"\n[bold green]✓ Successfully updated mdreader to version:[/bold green] [bold cyan]{latest}[/bold cyan] 🎉")
        return True
    except Exception as e:
        console.print(f"[bold red]Update error:[/bold red] {e}")
        return False
