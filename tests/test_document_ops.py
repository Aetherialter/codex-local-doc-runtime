from pathlib import Path

import fitz
import openpyxl
from docx import Document

from docrt.docx_ops import inspect_docx
from docrt.pdf_ops import inspect_pdf, render_pdf
from docrt.xlsx_ops import inspect_xlsx


def test_inspect_docx(tmp_path: Path):
    path = tmp_path / "sample.docx"
    document = Document()
    document.add_paragraph("hello docx")
    document.save(path)

    result = inspect_docx(path)

    assert result["paragraph_count"] == 1
    assert result["paragraphs"] == ["hello docx"]


def test_inspect_xlsx(tmp_path: Path):
    path = tmp_path / "sample.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet["A1"] = "hello"
    workbook.save(path)

    result = inspect_xlsx(path)

    assert result["sheet_count"] == 1
    assert result["sheets"][0]["preview"][0][0] == "hello"


def test_inspect_and_render_pdf(tmp_path: Path):
    path = tmp_path / "sample.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "hello pdf")
    document.save(path)
    document.close()

    info = inspect_pdf(path)
    rendered = render_pdf(path, tmp_path / "rendered")

    assert info["page_count"] == 1
    assert info["has_text_layer"] is True
    assert len(rendered["pages"]) == 1
