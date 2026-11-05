"""Tests for Office (Word / PowerPoint / Excel / CSV) → Markdown support."""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from office_samples import make_docx, make_pptx, make_xlsx  # noqa: E402

from mdreader.renderer.office import (  # noqa: E402
    office_to_markdown,
    is_office_file,
    get_office_type_label,
    read_document_text,
)


def test_office_file_detection():
    assert is_office_file("a.DOCX") and is_office_file(Path("x/b.pptx")) and is_office_file("c.xlsx")
    assert is_office_file("d.csv") and is_office_file("legacy.doc")
    assert not is_office_file("readme.md") and not is_office_file(None)
    assert get_office_type_label("a.docx") == "Word"
    assert get_office_type_label("a.pptx") == "PowerPoint"
    assert get_office_type_label("a.xlsx") == "Excel"
    assert get_office_type_label("a.md") is None


def test_docx_keeps_structure_in_document_order(tmp_path):
    """Headings must become Markdown headings (so the outline works), inline styles and
    nested lists survive, and tables stay in their original position between paragraphs."""
    md = office_to_markdown(make_docx(tmp_path / "a.docx"))
    assert "# 專案報告" in md
    assert "## 待辦事項" in md
    assert "**粗體**" in md and "*斜體*" in md
    assert "- 第一項\n  - 子項目" in md
    assert "| 項目 | 說明 |" in md
    # A literal pipe inside a cell must not split the table column
    assert "很長的說明 \\| 含管線符號" in md
    assert md.index("| 項目 |") < md.index("表格之後的段落")


def test_pptx_slides_become_outline_sections(tmp_path):
    """Each slide is a level-2 heading so the outline modal can jump between slides;
    bullet levels, tables and speaker notes are preserved."""
    md = office_to_markdown(make_pptx(tmp_path / "b.pptx"))
    assert "## Slide 1: 架構總覽" in md
    assert "## Slide 2: 時程表" in md
    assert "- 第一層重點\n  - 第二層細節" in md
    assert "> **Notes:** 講者備忘：強調沙盒" in md
    assert "| Phase 1 | 沙盒 |" in md
    # Title text must not be repeated as a bullet
    assert "- 架構總覽" not in md


def test_xlsx_sheets_trimmed_and_capped(tmp_path):
    """Each sheet is a section; far-away empty cells are trimmed; huge sheets are
    capped so the viewer does not freeze building thousands of table cells."""
    md = office_to_markdown(make_xlsx(tmp_path / "c.xlsx", big_rows=30), max_sheet_rows=10)
    assert "## Sheet: 營收 (2 rows × 3 cols)" in md
    assert "| 一月 | 100 | 2026-01-31 |" in md
    assert "| 二月 | 250 | 2026-02-28 |" in md  # 250.0 shown as integer
    assert "## Sheet: 空白頁" in md and "_(empty sheet)_" in md
    assert "## Sheet: 明細 (30 rows × 2 cols)" in md
    assert "| 9 | row9 |" in md and "| 10 | row10 |" not in md
    assert "Showing first 10 of 30 rows" in md
    revenue = md.split("## Sheet: 空白頁")[0]
    assert all(line.count("|") == 4 for line in revenue.splitlines() if line.startswith("|"))


def test_csv_big5_fallback(tmp_path):
    """CSV exported by Excel on zh-TW Windows is Big5; it must still be readable."""
    p = tmp_path / "data.csv"
    p.write_bytes("名稱,數量\n蘋果,3\n".encode("cp950"))
    md = office_to_markdown(p)
    assert "| 名稱 | 數量 |" in md and "| 蘋果 | 3 |" in md


def test_legacy_binary_format_shows_hint(tmp_path):
    p = tmp_path / "old.doc"
    p.write_bytes(b"\xd0\xcf\x11\xe0binary")
    assert ".docx" in read_document_text(p)


def test_tui_opens_office_files_as_markdown(tmp_path, monkeypatch):
    """Opening .docx/.pptx/.xlsx must not crash on binary bytes, must render through the
    Markdown viewer (not as a code block), expose slides/sheets in the outline and
    show the Office type in the status bar."""
    import mdreader.utils.config as config
    from mdreader.app import MDReaderApp
    from mdreader.widgets.markdown_view import MarkdownViewerWidget
    from textual.widgets._markdown import MarkdownTable, MarkdownFence

    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")
    docx_p = make_docx(tmp_path / "a.docx")
    pptx_p = make_pptx(tmp_path / "b.pptx")
    xlsx_p = make_xlsx(tmp_path / "c.xlsx")
    app = MDReaderApp(filepath=docx_p)

    async def run_check():
        async with app.run_test(size=(160, 40)) as pilot:
            await pilot.pause(0.3)
            viewer = app.query_one("#viewer")
            assert isinstance(viewer, MarkdownViewerWidget)
            assert list(viewer.query(MarkdownTable))
            assert not list(viewer.query(MarkdownFence))
            assert "Word" in str(app.query_one("#position-label").render())

            await app.open_file(pptx_p)
            await pilot.pause(0.3)
            headings = [h[1] if isinstance(h, tuple) else h for h in app.query_one("#viewer").get_headings()]
            assert any("Slide 2" in str(h) for h in headings)

            await app.open_file(xlsx_p)
            await pilot.pause(0.3)
            headings = [h[1] if isinstance(h, tuple) else h for h in app.query_one("#viewer").get_headings()]
            assert any("Sheet: 營收" in str(h) for h in headings)

    asyncio.run(run_check())


def test_cli_inline_renders_docx(tmp_path, monkeypatch, capsys):
    from mdreader import __main__ as cli

    p = make_docx(tmp_path / "a.docx")
    monkeypatch.setattr(sys, "argv", ["mdreader", "--inline", str(p)])
    cli.main()
    out = capsys.readouterr().out
    assert "專案報告" in out and "第一項" in out
    assert "PK" not in out  # raw zip bytes must never leak to the terminal
