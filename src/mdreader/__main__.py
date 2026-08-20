"""CLI Entrypoint for mdreader."""
import sys
import argparse
from pathlib import Path
from mdreader import __version__
from mdreader.app import MDReaderApp
from mdreader.renderer.mermaid import preprocess_mermaid
from rich.console import Console
from rich.markdown import Markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mdreader",
        description="Terminal Markdown previewer with Mermaid support — GUI-like experience in CLI",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to the markdown file to preview (reads from stdin if omitted or '-')",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-w", "--watch",
        action="store_true",
        help="Watch mode: auto-reload when file changes on disk",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=None,
        help="Cap content max width (in columns)",
    )
    parser.add_argument(
        "-t", "--theme",
        type=str,
        default=None,
        help="Set color theme (e.g. textual-dark, textual-light, tokyo-night, monokai, solarized-dark, nord)",
    )
    parser.add_argument(
        "--no-toc",
        action="store_true",
        help="Hide Table of Contents sidebar by default",
    )
    parser.add_argument(
        "--inline",
        action="store_true",
        help="Render Markdown directly to stdout without interactive TUI",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    content = ""
    filepath = None

    if args.file and args.file != "-":
        path = Path(args.file)
        if not path.is_file():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        filepath = path
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading file '{args.file}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        if not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            # If launched interactively without file arg, find markdown files
            md_files = list(Path(".").glob("*.md"))
            if md_files:
                filepath = md_files[0]
                content = filepath.read_text(encoding="utf-8")
            else:
                content = "# Welcome to mdreader\n\nNo markdown file specified. Press `o` to open the file picker or `q` to quit."

    if args.inline:
        # Non-interactive stdout rendering using rich
        console = Console(width=args.width)
        processed_md = preprocess_mermaid(content)
        md = Markdown(processed_md)
        console.print(md)
        return

    # Interactive TUI Mode
    app = MDReaderApp(
        content=content,
        filepath=filepath,
        max_width=args.width,
        watch=args.watch,
        theme=args.theme,
        show_toc=not args.no_toc,
    )
    app.run()


if __name__ == "__main__":
    main()
