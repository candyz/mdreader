"""Office document (Word / PowerPoint / Excel / CSV) to GFM Markdown conversion.

Office files are converted to Markdown at load time so they reuse the existing
Markdown viewer: wrapped tables, outline (headings = slides / sheets), search, export.
Heavy parser libraries are imported lazily to keep startup fast.
"""
from __future__ import annotations
import csv
import datetime
from pathlib import Path

WORD_EXTENSIONS = (".docx",)
POWERPOINT_EXTENSIONS = (".pptx",)
EXCEL_EXTENSIONS = (".xlsx", ".xlsm")
CSV_EXTENSIONS = (".csv", ".tsv")
PDF_EXTENSIONS = (".pdf",)
# Legacy binary formats: recognised so we show a conversion hint instead of garbled bytes
LEGACY_EXTENSIONS = (".doc", ".ppt", ".xls")
OFFICE_EXTENSIONS = (
    WORD_EXTENSIONS
    + POWERPOINT_EXTENSIONS
    + EXCEL_EXTENSIONS
    + CSV_EXTENSIONS
    + PDF_EXTENSIONS
    + LEGACY_EXTENSIONS
)

DEFAULT_MAX_SHEET_ROWS = 500


def _suffix(filepath_or_name: Path | str | None) -> str:
    if not filepath_or_name:
        return ""
    s = str(filepath_or_name).lower()
    if s.startswith(".") and "/" not in s and "\\" not in s and "." not in s[1:]:
        return s
    return Path(s).suffix.lower()


def is_office_file(filepath_or_name: Path | str | None) -> bool:
    """Check if the file is an Office document (or CSV) that is converted to Markdown."""
    return _suffix(filepath_or_name) in OFFICE_EXTENSIONS


def is_text_office_file(filepath_or_name: Path | str | None) -> bool:
    """CSV/TSV are plain text and can still be edited in a text editor."""
    return _suffix(filepath_or_name) in CSV_EXTENSIONS


def get_office_type_label(filepath_or_name: Path | str | None) -> str | None:
    """Return a status bar label ("Word" / "PowerPoint" / "Excel" / "CSV" / "PDF") or None."""
    ext = _suffix(filepath_or_name)
    if ext in (".docx", ".doc"):
        return "Word"
    if ext in (".pptx", ".ppt"):
        return "PowerPoint"
    if ext in (".xlsx", ".xlsm", ".xls"):
        return "Excel"
    if ext in CSV_EXTENSIONS:
        return "CSV"
    if ext in PDF_EXTENSIONS:
        return "PDF"
    return None


def read_document_text(filepath: Path) -> str:
    """Read a file for display: Office documents are converted to Markdown, others read as UTF-8."""
    if is_office_file(filepath):
        return office_to_markdown(filepath)
    return filepath.read_text(encoding="utf-8")


def office_to_markdown(filepath: Path, max_sheet_rows: int = DEFAULT_MAX_SHEET_ROWS) -> str:
    """Convert an Office or PDF document to GFM Markdown."""
    filepath = Path(filepath)
    ext = filepath.suffix.lower()
    if ext in WORD_EXTENSIONS:
        return _docx_to_markdown(filepath)
    if ext in POWERPOINT_EXTENSIONS:
        return _pptx_to_markdown(filepath)
    if ext in EXCEL_EXTENSIONS:
        return _xlsx_to_markdown(filepath, max_sheet_rows)
    if ext in CSV_EXTENSIONS:
        return _csv_to_markdown(filepath, max_sheet_rows)
    if ext in PDF_EXTENSIONS:
        return _pdf_to_markdown(filepath)
    if ext in LEGACY_EXTENSIONS:
        new_ext = {".doc": ".docx", ".ppt": ".pptx", ".xls": ".xlsx"}[ext]
        return (
            f"# {filepath.name}\n\n"
            f"> ⚠️ 不支援舊版二進位格式 `{ext}`（Legacy binary format is not supported）。\n"
            f">\n"
            f"> 請用 Office / LibreOffice 另存為 `{new_ext}` 後再開啟。\n"
        )
    raise ValueError(f"Not an Office document: {filepath.name}")


# ---------------------------------------------------------------- helpers

def _cell_text(value: object) -> str:
    """Format a cell value for a single-line GFM table cell."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, datetime.datetime):
        if value.time() == datetime.time(0, 0):
            return value.date().isoformat()
        return value.isoformat(sep=" ")
    if isinstance(value, (datetime.date, datetime.time)):
        return value.isoformat()
    text = str(value)
    return " ".join(text.split()).replace("|", "\\|")


def _rows_to_table(rows: list[list[str]]) -> str:
    """Render rows (first row = header) as a GFM pipe table."""
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    padded = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(padded[0]) + " |", "|" + "---|" * width]
    for r in padded[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


def _trim_table(rows: list[list[str]]) -> list[list[str]]:
    """Drop trailing empty rows and trailing empty columns (common in spreadsheets)."""
    while rows and not any(c.strip() for c in rows[-1]):
        rows.pop()
    if not rows:
        return rows
    width = 0
    for r in rows:
        for i in range(len(r) - 1, -1, -1):
            if r[i].strip():
                width = max(width, i + 1)
                break
    return [r[:width] for r in rows]


def _wrap_inline(text: str, marker: str) -> str:
    """Wrap text with a Markdown emphasis marker, keeping surrounding whitespace outside."""
    stripped = text.strip()
    if not stripped:
        return text
    lead = text[: len(text) - len(text.lstrip())]
    trail = text[len(text.rstrip()):]
    return f"{lead}{marker}{stripped}{marker}{trail}"


# ---------------------------------------------------------------- Word

def _docx_paragraph_inline(paragraph) -> str:
    """Convert paragraph runs/hyperlinks to inline Markdown, merging runs of equal style."""
    from docx.text.hyperlink import Hyperlink

    segments: list[list] = []  # [text, bold, italic, href]
    for item in paragraph.iter_inner_content():
        if isinstance(item, Hyperlink):
            href = item.address or ""
            text = item.text
            bold = italic = False
        else:
            href = ""
            text = item.text
            bold = bool(item.bold)
            italic = bool(item.italic)
        if not text:
            continue
        if segments and segments[-1][1:] == [bold, italic, href]:
            segments[-1][0] += text
        else:
            segments.append([text, bold, italic, href])

    parts = []
    for text, bold, italic, href in segments:
        if href:
            parts.append(f"[{text.strip()}]({href})" if text.strip() else text)
            continue
        if bold:
            text = _wrap_inline(text, "**")
        if italic:
            text = _wrap_inline(text, "*")
        parts.append(text)
    return "".join(parts).replace("\n", " ").strip()


def _docx_list_level(paragraph) -> int | None:
    """Return the list nesting level of a paragraph, or None if it is not a list item."""
    style_name = (paragraph.style.name if paragraph.style is not None else "") or ""
    p_pr = paragraph._p.pPr
    num_pr = p_pr.numPr if p_pr is not None else None
    if num_pr is not None and num_pr.ilvl is not None:
        return int(num_pr.ilvl.val)
    if num_pr is not None or style_name.startswith("List"):
        # "List Bullet 2" -> level 1
        last = style_name.split()[-1] if style_name else ""
        return int(last) - 1 if last.isdigit() else 0
    return None


def _docx_to_markdown(filepath: Path) -> str:
    import docx
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    document = docx.Document(str(filepath))
    blocks: list[str] = []
    list_lines: list[str] = []

    def flush_list() -> None:
        if list_lines:
            blocks.append("\n".join(list_lines))
            list_lines.clear()

    for child in document.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            paragraph = Paragraph(child, document)
            text = _docx_paragraph_inline(paragraph)
            if not text:
                continue
            style_name = (paragraph.style.name if paragraph.style is not None else "") or ""
            if style_name == "Title":
                flush_list()
                blocks.append(f"# {text}")
                continue
            if style_name.startswith("Heading"):
                level = style_name.split()[-1]
                if level.isdigit():
                    flush_list()
                    blocks.append("#" * min(6, int(level)) + " " + text)
                    continue
            list_level = _docx_list_level(paragraph)
            if list_level is not None:
                marker = "1." if "Number" in style_name else "-"
                list_lines.append("  " * list_level + f"{marker} {text}")
                continue
            flush_list()
            blocks.append(text)
        elif tag == "tbl":
            flush_list()
            table = Table(child, document)
            rows = [[_cell_text(cell.text) for cell in row.cells] for row in table.rows]
            rows = _trim_table(rows)
            if rows:
                blocks.append(_rows_to_table(rows))
    flush_list()
    if not blocks:
        return f"# {filepath.name}\n\n_(empty document)_\n"
    return "\n\n".join(blocks) + "\n"


# ---------------------------------------------------------------- PowerPoint

def _pptx_shape_blocks(shape, title_shape_id) -> list[str]:
    """Convert a slide shape (text frame / table / group) to Markdown blocks."""
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        blocks: list[str] = []
        for sub in _pptx_sorted_shapes(shape.shapes):
            blocks.extend(_pptx_shape_blocks(sub, title_shape_id))
        return blocks
    if getattr(shape, "has_table", False) and shape.has_table:
        rows = [[_cell_text(cell.text) for cell in row.cells] for row in shape.table.rows]
        rows = _trim_table(rows)
        return [_rows_to_table(rows)] if rows else []
    if shape.has_text_frame and shape.shape_id != title_shape_id:
        lines = []
        for para in shape.text_frame.paragraphs:
            text = " ".join("".join(run.text for run in para.runs).split())
            if text:
                lines.append("  " * para.level + f"- {text}")
        return ["\n".join(lines)] if lines else []
    return []


def _pptx_sorted_shapes(shapes) -> list:
    """Order shapes in reading order (top-to-bottom, then left-to-right)."""
    return sorted(shapes, key=lambda s: ((s.top or 0), (s.left or 0)))


def _pptx_to_markdown(filepath: Path) -> str:
    import pptx

    presentation = pptx.Presentation(str(filepath))
    sections: list[str] = []
    for index, slide in enumerate(presentation.slides, 1):
        title_shape = slide.shapes.title
        title = " ".join(title_shape.text.split()) if title_shape is not None else ""
        title_id = title_shape.shape_id if title_shape is not None else None
        blocks = [f"## Slide {index}: {title}" if title else f"## Slide {index}"]
        for shape in _pptx_sorted_shapes(slide.shapes):
            blocks.extend(_pptx_shape_blocks(shape, title_id))
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip() if slide.notes_slide.notes_text_frame else ""
            if notes:
                note_lines = [line.strip() for line in notes.splitlines() if line.strip()]
                blocks.append("> **Notes:** " + "\n>\n> ".join(note_lines))
        sections.append("\n\n".join(blocks))
    if not sections:
        return f"# {filepath.name}\n\n_(empty presentation)_\n"
    return "\n\n---\n\n".join(sections) + "\n"


# ---------------------------------------------------------------- Excel / CSV

def _table_section(heading: str, raw_rows, max_rows: int) -> str:
    """Build a sheet section from a row iterator, keeping only the first max_rows rows."""
    kept: list[list[str]] = []
    last_nonempty = 0
    total = 0
    for row in raw_rows:
        total += 1
        cells = [_cell_text(v) for v in row]
        if any(cells):
            last_nonempty = total
        if len(kept) <= max_rows:  # header + max_rows data rows
            kept.append(cells)
    kept = _trim_table(kept)
    if not kept:
        return f"{heading}\n\n_(empty sheet)_"
    data_rows = max(0, last_nonempty - 1)
    cols = max(len(r) for r in kept)
    parts = [f"{heading} ({data_rows} rows × {cols} cols)", _rows_to_table(kept)]
    if data_rows > max_rows:
        parts.append(f"> ⚠️ Showing first {max_rows} of {data_rows} rows.")
    return "\n\n".join(parts)


def _xlsx_to_markdown(filepath: Path, max_rows: int) -> str:
    import openpyxl

    workbook = openpyxl.load_workbook(str(filepath), read_only=True, data_only=True)
    try:
        sections = [
            _table_section(f"## Sheet: {ws.title}", ws.iter_rows(values_only=True), max_rows)
            for ws in workbook.worksheets
        ]
    finally:
        workbook.close()
    return "\n\n".join(sections) + "\n"


def _csv_to_markdown(filepath: Path, max_rows: int) -> str:
    delimiter = "\t" if filepath.suffix.lower() == ".tsv" else ","
    try:
        text = filepath.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        # Excel on Traditional Chinese Windows exports CSV as Big5 (cp950)
        text = filepath.read_text(encoding="cp950", errors="replace")
    rows = csv.reader(text.splitlines(), delimiter=delimiter)
    return _table_section(f"## {filepath.name}", rows, max_rows) + "\n"


# ---------------------------------------------------------------- PDF

def _pdf_to_markdown(filepath: Path) -> str:
    import re
    import pypdf

    reader = pypdf.PdfReader(str(filepath))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            pass
        if reader.is_encrypted:
            return (
                f"# {filepath.name}\n\n"
                f"> 🔒 此 PDF 檔案受密碼保護，無法直接預覽（Password-protected PDF）。\n"
            )

    total_pages = len(reader.pages)
    if total_pages == 0:
        return f"# {filepath.name}\n\n_(empty PDF document)_\n"

    sections: list[str] = []
    meta = reader.metadata
    if meta:
        title = getattr(meta, "title", None)
        author = getattr(meta, "author", None)
        meta_parts = []
        if title and str(title).strip():
            meta_parts.append(f"**Title:** {str(title).strip()}")
        if author and str(author).strip():
            meta_parts.append(f"**Author:** {str(author).strip()}")
        if meta_parts:
            sections.append(f"# {filepath.name}\n\n> " + " │ ".join(meta_parts))

    for index, page in enumerate(reader.pages, 1):
        heading = f"## Page {index} / {total_pages}"
        try:
            raw_text = (page.extract_text() or "").strip()
        except Exception:
            raw_text = ""
        if not raw_text:
            sections.append(f"{heading}\n\n_(no extractable text on this page)_")
            continue
        cleaned = re.sub(r"\n{3,}", "\n\n", raw_text)
        sections.append(f"{heading}\n\n{cleaned}")

    return "\n\n---\n\n".join(sections) + "\n"
