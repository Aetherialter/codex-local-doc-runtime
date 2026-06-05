from __future__ import annotations

import json
from pathlib import Path

import fitz
import pytest

from docrt.config import Config
from docrt.models import ErrorCode
from docrt.paths import ValidationError
from docrt.pdf_annotate import annotate_pdf
from docrt.recovery import recovery_actions
from docrt.schema_ops import validate_patch, validate_result, validate_task
from docrt.storage_ops import clean, storage_report


def _make_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "annotate me")
    document.save(path)
    document.close()


def test_recovery_actions_cover_common_errors() -> None:
    for code in (
        ErrorCode.FILE_NOT_FOUND.value,
        ErrorCode.FILE_LOCKED.value,
        ErrorCode.WORD_COM_UNAVAILABLE.value,
        ErrorCode.POPPLER_UNAVAILABLE.value,
        ErrorCode.VALIDATION_FAILED.value,
    ):
        assert recovery_actions(code)


def test_schema_validation_for_patch_task_and_result(tmp_path: Path) -> None:
    patch_path = tmp_path / "patch.json"
    task_path = tmp_path / "task.json"
    result_path = tmp_path / "result.json"
    patch_path.write_text(
        json.dumps(
            {
                "document_type": "docx",
                "operations": [{"type": "replace_text", "find": "Draft", "replace": "Ready"}],
            }
        ),
        encoding="utf-8",
    )
    task_path.write_text(
        json.dumps({"task": "read-docx", "input": "sample.docx", "dry_run": True}),
        encoding="utf-8",
    )
    result_path.write_text(
        json.dumps(
            {
                "ok": True,
                "operation": "doctor",
                "run_id": "test",
                "started_at": "now",
                "ended_at": "now",
                "duration_ms": 0,
                "data": {},
            }
        ),
        encoding="utf-8",
    )

    assert validate_patch(patch_path)["valid"] is True
    assert validate_task(task_path)["valid"] is True
    assert validate_result(result_path)["valid"] is True


def test_schema_validation_rejects_non_object(tmp_path: Path) -> None:
    path = tmp_path / "patch.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(ValidationError):
        validate_patch(path)


def test_pdf_annotation_writes_output(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.pdf"
    annotations_path = tmp_path / "annotations.json"
    output_path = tmp_path / "annotated.pdf"
    _make_pdf(input_path)
    annotations_path.write_text(
        json.dumps(
            {
                "annotations": [
                    {"type": "rectangle", "page_number": 1, "bbox": [60, 60, 180, 90]},
                    {
                        "type": "text_note",
                        "page_number": 1,
                        "point": [72, 120],
                        "text": "Review",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    result = annotate_pdf(input_path, annotations_path, output_path)

    assert result["annotation_count"] == 2
    assert output_path.exists()


def test_storage_report_and_clean_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work")
    log_path = tmp_path / "logs" / "run.jsonl"
    log_path.parent.mkdir()
    log_path.write_text("{}", encoding="utf-8")

    report = storage_report(config)
    planned = clean(config, logs=True)

    assert any(target["name"] == "logs" for target in report["targets"])
    assert planned["dry_run"] is True
    assert planned["planned_count"] == 1
    assert log_path.exists()
