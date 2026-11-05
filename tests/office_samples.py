"""Build sample Office files for manual / automated checks."""
from __future__ import annotations
from pathlib import Path


def make_docx(path: Path) -> Path:
    import docx
    d = docx.Document()
    d.add_heading("專案報告", level=1)
    p = d.add_paragraph("這是 ")
    p.add_run("粗體").bold = True
    p.add_run(" 與 ")
    p.add_run("斜體").italic = True
    p.add_run(" 文字。")
    d.add_heading("待辦事項", level=2)
    d.add_paragraph("第一項", style="List Bullet")
    d.add_paragraph("子項目", style="List Bullet 2")
    d.add_paragraph("步驟一", style="List Number")
    t = d.add_table(rows=3, cols=2)
    for r, row in enumerate([("項目", "說明"), ("A", "很長的說明 | 含管線符號"), ("B", "第二列")]):
        for c, val in enumerate(row):
            t.cell(r, c).text = val
    d.add_paragraph("表格之後的段落")
    d.save(str(path))
    return path


def make_pptx(path: Path) -> Path:
    import pptx
    from pptx.util import Inches
    prs = pptx.Presentation()
    s1 = prs.slides.add_slide(prs.slide_layouts[1])
    s1.shapes.title.text = "架構總覽"
    body = s1.placeholders[1].text_frame
    body.text = "第一層重點"
    p = body.add_paragraph()
    p.text = "第二層細節"
    p.level = 1
    s1.notes_slide.notes_text_frame.text = "講者備忘：強調沙盒"
    s2 = prs.slides.add_slide(prs.slide_layouts[5])
    s2.shapes.title.text = "時程表"
    tbl = s2.shapes.add_table(2, 2, Inches(1), Inches(2), Inches(6), Inches(1)).table
    tbl.cell(0, 0).text = "階段"
    tbl.cell(0, 1).text = "內容"
    tbl.cell(1, 0).text = "Phase 1"
    tbl.cell(1, 1).text = "沙盒"
    prs.save(str(path))
    return path


def make_xlsx(path: Path, big_rows: int = 0) -> Path:
    import openpyxl
    import datetime
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "營收"
    ws.append(["月份", "金額", "日期"])
    ws.append(["一月", 100, datetime.datetime(2026, 1, 31)])
    ws.append(["二月", 250.0, datetime.datetime(2026, 2, 28)])
    ws["B4"] = "=SUM(B2:B3)"
    ws["Z50"] = None  # touch a far cell; must be trimmed
    ws2 = wb.create_sheet("空白頁")
    ws3 = wb.create_sheet("明細")
    ws3.append(["id", "name"])
    for i in range(big_rows):
        ws3.append([i, f"row{i}"])
    wb.save(str(path))
    return path


def make_pdf(path: Path) -> Path:
    import pypdf
    from pypdf.generic import NameObject, DictionaryObject, DecodedStreamObject

    writer = pypdf.PdfWriter()
    writer.add_metadata({"/Title": "Architecture Spec", "/Author": "SW Team"})
    for text in ("First page content hello world", "Second page content phase two"):
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        })
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})
        })
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 14 Tf 72 720 Td ({text}) Tj ET".encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)
    with open(path, "wb") as f:
        writer.write(f)
    return path
