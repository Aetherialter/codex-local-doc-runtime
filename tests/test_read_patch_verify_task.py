import json
from pathlib import Path

import fitz
import openpyxl
import pytest
from docx import Document

from docrt.config import Config
from docrt.models import ErrorCode
from docrt.patch_ops import patch_docx, patch_xlsx
from docrt.paths import ValidationError
from docrt.read_ops import read_docx, read_pdf, read_xlsx
from docrt.task_ops import run_task_manifest
from docrt.verify_ops import verify_docx, verify_xlsx


def _make_docx(path: Path) -> None:
    document = Document()
    document.add_paragraph("hello docx")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Field"
    table.cell(0, 1).text = "Value"
    table.cell(1, 0).text = "Status"
    table.cell(1, 1).text = "Draft"
    document.save(path)


def _make_xlsx(path: Path) -> None:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Summary"
    sheet.append(["Field", "Value"])
    sheet.append(["Status", "Draft"])
    workbook.save(path)


def _make_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "hello pdf")
    document.save(path)
    document.close()


def test_read_docx_protocol(tmp_path: Path):
    path = tmp_path / "sample.docx"
    _make_docx(path)

    result = read_docx(path)

    assert result["document_type"] == "docx"
    assert result["metadata"]["paragraph_count"] == 1
    assert result["content_blocks"][0]["type"] == "paragraph"
    assert result["tables"][0]["rows"][1][1]["text"] == "Draft"


def test_read_pdf_protocol(tmp_path: Path):
    path = tmp_path / "sample.pdf"
    _make_pdf(path)

    result = read_pdf(path)

    assert result["document_type"] == "pdf"
    assert result["metadata"]["page_count"] == 1
    assert result["metadata"]["has_text_layer"] is True
    assert result["content_blocks"][0]["type"] == "page_text"


def test_read_xlsx_protocol(tmp_path: Path):
    path = tmp_path / "sample.xlsx"
    _make_xlsx(path)

    result = read_xlsx(path)

    assert result["document_type"] == "xlsx"
    assert result["metadata"]["sheet_count"] == 1
    assert result["content_blocks"][0]["location"]["sheet"] == "Summary"


def test_patch_docx_and_verify(tmp_path: Path):
    input_path = tmp_path / "sample.docx"
    patch_path = tmp_path / "patch.json"
    output_path = tmp_path / "patched.docx"
    _make_docx(input_path)
    patch_path.write_text(
        json.dumps(
            {
                "document_type": "docx",
                "operations": [
                    {"type": "replace_text", "find": "hello", "replace": "patched"},
                    {
                        "type": "replace_table_cell",
                        "table_index": 0,
                        "row_index": 1,
                        "column_index": 1,
                        "text": "Ready",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    patched = patch_docx(input_path, patch_path, output_path)
    verification = verify_docx(input_path, output_path)
    read_back = read_docx(output_path)

    assert patched["patch_summary"]["operation_count"] == 2
    assert patched["patch_summary"]["applied_count"] == 2
    assert verification["changed"] is True
    assert verification["changed_blocks"]
    assert "patched docx" in read_back["content_blocks"][0]["text"]
    assert read_back["tables"][0]["rows"][1][1]["text"] == "Ready"


def test_patch_xlsx_and_verify(tmp_path: Path):
    input_path = tmp_path / "sample.xlsx"
    patch_path = tmp_path / "patch.json"
    output_path = tmp_path / "patched.xlsx"
    _make_xlsx(input_path)
    patch_path.write_text(
        json.dumps(
            {
                "document_type": "xlsx",
                "operations": [
                    {"type": "set_cell", "sheet": "Summary", "cell": "B2", "value": "Ready"},
                    {"type": "add_sheet", "name": "Notes"},
                    {"type": "rename_sheet", "old_name": "Notes", "new_name": "Review"},
                ],
            }
        ),
        encoding="utf-8",
    )

    patched = patch_xlsx(input_path, patch_path, output_path)
    verification = verify_xlsx(input_path, output_path)
    read_back = read_xlsx(output_path)

    assert patched["patch_summary"]["operation_count"] == 3
    assert patched["patch_summary"]["applied_count"] == 3
    assert verification["changed"] is True
    assert verification["changed_cells"]
    assert any(block["text"] == "Ready" for block in read_back["content_blocks"])
    assert "Review" in [sheet["name"] for sheet in read_back["metadata"]["sheets"]]


def test_patch_docx_dry_run_does_not_write_output(tmp_path: Path):
    input_path = tmp_path / "sample.docx"
    patch_path = tmp_path / "patch.json"
    output_path = tmp_path / "patched.docx"
    _make_docx(input_path)
    patch_path.write_text(
        json.dumps(
            {
                "document_type": "docx",
                "operations": [
                    {
                        "type": "replace_paragraph",
                        "paragraph_index": 0,
                        "expected_text": "hello docx",
                        "text": "planned docx",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = patch_docx(input_path, patch_path, output_path, dry_run=True)

    assert result["dry_run"] is True
    assert result["verification"] is None
    assert result["patch_summary"]["planned_count"] == 1
    assert result["patch_summary"]["applied_count"] == 0
    assert result["patch_summary"]["planned_changes"]
    assert not output_path.exists()


def test_patch_xlsx_expected_value_mismatch_fails(tmp_path: Path):
    input_path = tmp_path / "sample.xlsx"
    patch_path = tmp_path / "patch.json"
    output_path = tmp_path / "patched.xlsx"
    _make_xlsx(input_path)
    patch_path.write_text(
        json.dumps(
            {
                "document_type": "xlsx",
                "operations": [
                    {
                        "type": "set_cell",
                        "sheet": "Summary",
                        "cell": "B2",
                        "expected_value": "Published",
                        "value": "Ready",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError) as exc_info:
        patch_xlsx(input_path, patch_path, output_path)

    assert exc_info.value.error_code == ErrorCode.VALIDATION_FAILED


def test_patch_rejects_invalid_json(tmp_path: Path):
    input_path = tmp_path / "sample.docx"
    patch_path = tmp_path / "patch.json"
    output_path = tmp_path / "patched.docx"
    _make_docx(input_path)
    patch_path.write_text("{", encoding="utf-8")

    with pytest.raises(ValidationError) as exc_info:
        patch_docx(input_path, patch_path, output_path)

    assert exc_info.value.error_code == ErrorCode.VALIDATION_FAILED


def test_run_task_dry_run(tmp_path: Path):
    manifest_path = tmp_path / "task.json"
    manifest_path.write_text(
        json.dumps(
            {
                "task": "read-docx",
                "input": "examples/fixtures/sample.docx",
                "dry_run": True,
            }
        ),
        encoding="utf-8",
    )

    result = run_task_manifest(manifest_path, Config.load(project_root=tmp_path), "test-run")

    assert result["dry_run"] is True
    assert result["would_execute"]["task"] == "read-docx"


def test_run_task_multi_step_with_reference(tmp_path: Path):
    input_path = tmp_path / "sample.xlsx"
    patch_path = tmp_path / "patch.json"
    output_path = tmp_path / "patched.xlsx"
    manifest_path = tmp_path / "task.json"
    _make_xlsx(input_path)
    patch_path.write_text(
        json.dumps(
            {
                "document_type": "xlsx",
                "operations": [
                    {
                        "type": "set_cell",
                        "sheet": "Summary",
                        "cell": "B2",
                        "expected_value": "Draft",
                        "value": "Ready",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(
            {
                "stop_on_error": True,
                "tasks": [
                    {
                        "id": "patch",
                        "task": "patch-xlsx",
                        "input": str(input_path),
                        "patch": str(patch_path),
                        "output": str(output_path),
                    },
                    {
                        "id": "verify",
                        "task": "verify-xlsx",
                        "before": str(input_path),
                        "after": "${steps.patch.output_path}",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    result = run_task_manifest(manifest_path, Config.load(project_root=tmp_path), "test-run")

    assert result["failed_count"] == 0
    assert result["success_count"] == 2
    assert result["steps"][1]["result"]["changed"] is True


def test_run_task_rejects_unknown_task(tmp_path: Path):
    manifest_path = tmp_path / "task.json"
    manifest_path.write_text(json.dumps({"task": "unknown", "input": "x"}), encoding="utf-8")

    with pytest.raises(ValidationError) as exc_info:
        run_task_manifest(manifest_path, Config.load(project_root=tmp_path), "test-run")

    assert exc_info.value.error_code == ErrorCode.VALIDATION_FAILED
