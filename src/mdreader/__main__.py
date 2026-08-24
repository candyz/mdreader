"""CLI Entrypoint for mdreader."""
from __future__ import annotations
import sys
import argparse
from pathlib import Path
from mdreader import __version__
from mdreader.app import MDReaderApp
from mdreader.renderer.mermaid import preprocess_mermaid
from mdreader.renderer.html import html_to_markdown, is_html_content, is_markdown_file, detect_code_language
from rich.console import Console
from rich.markdown import Markdown


from mdreader.utils.export import export_document_to_file


def parse_args(argv: list[str] | None = None) -> tuple[argparse.Namespace, int | None]:
    if argv is None:
        argv = sys.argv[1:]

    # Extract vim-style +<line> syntax (e.g. mdreader +50 README.md)
    plus_line = None
    filtered_argv = []
    for arg in argv:
        if arg.startswith("+") and arg[1:].isdigit():
            plus_line = int(arg[1:])
        else:
            filtered_argv.append(arg)

    parser = argparse.ArgumentParser(
        prog="mdreader",
        description="Terminal Markdown & Text reader with Mermaid support and Gigabit performance — GUI-like experience in CLI",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to the file to preview (reads from stdin if omitted or '-')",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-l", "--line",
        type=int,
        default=None,
        help="Jump directly to line number on startup (1-indexed, e.g. -l 42 or +42)",
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
        help="Set color theme (e.g. github-dark, github-light, textual-dark, textual-light, tokyo-night, monokai, solarized-dark, dracula, nord)",
    )
    parser.add_argument(
        "--list-themes",
        action="store_true",
        help="List all available built-in color themes and exit",
    )
    parser.add_argument(
        "--toc",
        action="store_true",
        help="Show Table of Contents outline sidebar on startup",
    )
    parser.add_argument(
        "--export-html",
        type=str,
        default=None,
        metavar="OUT_HTML",
        help="Export document directly to standalone HTML file without launching TUI",
    )
    parser.add_argument(
        "--export-txt",
        type=str,
        default=None,
        metavar="OUT_TXT",
        help="Export document directly to plain text file without launching TUI",
    )
    parser.add_argument(
        "--inline",
        action="store_true",
        help="Render Markdown directly to stdout without interactive TUI",
    )
    args = parser.parse_args(filtered_argv)
    initial_line = plus_line if plus_line is not None else args.line
    return args, initial_line


def main() -> None:
    args, initial_line = parse_args()

    if args.list_themes:
        print(f"mdreader v{__version__} - Available Color Themes:")
        for t in MDReaderApp.THEME_LIST:
            print(f"  • {t}")
        return

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

    # Direct CLI Export Mode
    if args.export_html:
        out_p = export_document_to_file(content, args.export_html, export_format="html", title=filepath.stem if filepath else "Document")
        print(f"✅ Successfully exported standalone HTML: {out_p}")
        return
    if args.export_txt:
        out_p = export_document_to_file(content, args.export_txt, export_format="txt", title=filepath.stem if filepath else "Document")
        print(f"✅ Successfully exported plain text: {out_p}")
        return

    if args.inline:
        # Non-interactive stdout rendering using rich
        console = Console(width=args.width)
        raw_text = content
        fname = str(filepath.name) if filepath else None
        if is_html_content(raw_text, fname):
            raw_text = html_to_markdown(raw_text)
        elif fname and not is_markdown_file(fname):
            lang = detect_code_language(fname)
            raw_text = f"```{lang}\n{raw_text}\n```"
        processed_md = preprocess_mermaid(raw_text)
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
        show_toc=args.toc,
        initial_line=initial_line,
    )
    app.run()


if __name__ == "__main__":
    main()
