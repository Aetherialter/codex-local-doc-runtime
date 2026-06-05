import json
from pathlib import Path

import fitz
import openpyxl
from docx import Document
from typer.testing import CliRunner

from docrt.cli import app

runner = CliRunner()


def test_inspect_docx_output_option_writes_explicit_json(tmp_path: Path):
    input_path = tmp_path / "sample.docx"
    output_path = tmp_path / "custom" / "docx.json"
    document = Document()
    document.add_paragraph("hello docx")
    document.save(input_path)

    result = runner.invoke(app, ["inspect-docx", str(input_path), "--output", str(output_path)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["output_path"] == str(output_path.resolve())
    assert saved["paragraphs"] == ["hello docx"]


def test_inspect_pdf_output_option_writes_explicit_json(tmp_path: Path):
    input_path = tmp_path / "sample.pdf"
    output_path = tmp_path / "custom" / "pdf.json"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "hello pdf")
    document.save(input_path)
    document.close()

    result = runner.invoke(app, ["inspect-pdf", str(input_path), "--output", str(output_path)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["output_path"] == str(output_path.resolve())
    assert saved["page_count"] == 1


def test_inspect_xlsx_output_option_writes_explicit_json(tmp_path: Path):
    input_path = tmp_path / "sample.xlsx"
    output_path = tmp_path / "custom" / "xlsx.json"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet["A1"] = "hello xlsx"
    workbook.save(input_path)

    result = runner.invoke(app, ["inspect-xlsx", str(input_path), "--output", str(output_path)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["output_path"] == str(output_path.resolve())
    assert saved["sheets"][0]["preview"][0][0] == "hello xlsx"
