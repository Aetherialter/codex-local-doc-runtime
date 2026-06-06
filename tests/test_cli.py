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


def test_search_pdf_command_outputs_matches(tmp_path: Path):
    input_path = tmp_path / "sample.pdf"
    output_path = tmp_path / "custom" / "pdf-search.json"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "hello searchable pdf")
    document.save(input_path)
    document.close()

    result = runner.invoke(
        app,
        ["search-pdf", str(input_path), "searchable", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["operation"] == "search-pdf"
    assert payload["data"]["count"] == 1
    assert saved["matches"][0]["page_number"] == 1


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


def test_agent_config_command_outputs_json(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["agent-config"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["operation"] == "agent-config"
    assert payload["data"]["runtime"]["package"] == "docrt"
    assert "AGENTS.md" in payload["data"]["agents_md"]


def test_explain_task_command_outputs_json(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    task_path = tmp_path / "task.json"
    task_path.write_text(
        json.dumps({"task": "read-docx", "input": "sample.docx", "dry_run": True}),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["explain-task", str(task_path)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["operation"] == "explain-task"
    assert payload["data"]["reads"] == ["sample.docx"]


def test_batch_fingerprint_command_outputs_json(tmp_path: Path):
    docx_path = tmp_path / "sample.docx"
    xlsx_path = tmp_path / "sample.xlsx"
    document = Document()
    document.add_paragraph("hello docx")
    document.save(docx_path)
    workbook = openpyxl.Workbook()
    workbook.save(xlsx_path)

    result = runner.invoke(app, ["batch-fingerprint", str(docx_path), str(xlsx_path)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["operation"] == "batch-fingerprint"
    assert payload["data"]["count"] == 2
    assert payload["data"]["backend"] in {"python", "rust"}


def test_clean_command_omits_file_list_by_default(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_path = tmp_path / "logs" / "old.jsonl"
    log_path.parent.mkdir()
    log_path.write_text("{}", encoding="utf-8")

    result = runner.invoke(app, ["clean", "--logs"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["files"] == []
    assert payload["data"]["files_omitted"] >= 1


def test_analyze_logs_command_outputs_recommendations(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    error_log = tmp_path / "logs" / "errors" / "2026-06-06.error.jsonl"
    error_log.parent.mkdir(parents=True)
    error_log.write_text(
        json.dumps(
            {
                "timestamp": "2026-06-06T00:00:00.000Z",
                "operation": "patch-docx",
                "module": "docrt.patch_ops",
                "error_code": "VALIDATION_FAILED",
                "exception_type": "ValidationError",
                "message": "expected_text mismatch",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["analyze-logs", "--days", "30"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["operation"] == "analyze-logs"
    assert payload["data"]["issue_count"] == 1
    assert payload["data"]["recommendations"]
