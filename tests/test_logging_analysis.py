from __future__ import annotations

import json
from pathlib import Path

from docrt.config import Config
from docrt.errors import build_error_event
from docrt.log_analysis import analyze_logs
from docrt.logging import JsonlLogger
from docrt.models import ErrorCode
from docrt.paths import ValidationError
from docrt.runner import run_operation


def test_jsonl_logger_degrades_when_parent_is_not_directory(tmp_path: Path) -> None:
    blocked = tmp_path / "blocked"
    blocked.write_text("not a directory", encoding="utf-8")
    logger = JsonlLogger(blocked / "run.jsonl")

    logger.write({"event": "should not raise"})

    assert logger.degraded is True
    assert logger.status()["last_error"]


def test_run_operation_writes_error_event_and_diagnostic(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work")

    def fail(_run_id, _config, _logger):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "bad patch")

    result = run_operation("patch-docx", fail, config=config, backend="python")

    assert result.ok is False
    assert result.error_code == ErrorCode.VALIDATION_FAILED.value
    error_logs = list((tmp_path / "logs" / "errors").glob("*.error.jsonl"))
    assert len(error_logs) == 1
    event = json.loads(error_logs[0].read_text(encoding="utf-8").splitlines()[0])
    assert event["operation"] == "patch-docx"
    assert event["error_code"] == ErrorCode.VALIDATION_FAILED.value
    assert Path(str(result.diagnostic_report_path)).exists()


def test_analyze_logs_groups_errors_and_recommends_fixes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work")
    log_path = tmp_path / "logs" / "errors" / "2026-06-06.error.jsonl"
    log_path.parent.mkdir(parents=True)
    events = [
        {
            "timestamp": "2026-06-06T00:00:00.000Z",
            "operation": "patch-docx",
            "module": "docrt.patch_ops",
            "error_code": "VALIDATION_FAILED",
            "exception_type": "ValidationError",
            "message": r"expected_text mismatch at D:\project\python\secret\sample.docx",
        },
        {
            "timestamp": "2026-06-06T00:01:00.000Z",
            "operation": "patch-docx",
            "module": "docrt.patch_ops",
            "error_code": "VALIDATION_FAILED",
            "exception_type": "ValidationError",
            "message": "expected_text mismatch",
        },
    ]
    log_path.write_text(
        "\n".join(json.dumps(event) for event in events) + "\n",
        encoding="utf-8",
    )

    result = analyze_logs(config, days=30)

    assert result["scanned_error_events"] == 2
    assert result["issues"][0]["issue_id"] == "VALIDATION_FAILED:patch-docx"
    assert result["issues"][0]["count"] == 2
    assert "D:\\project\\python\\secret" not in result["issues"][0]["sample_message"]
    assert result["recommendations"][0]["suggested_fix"]["files"]
    assert result["recommendations"][0]["affected_operations"] == ["patch-docx"]


def test_error_event_sanitizes_windows_paths() -> None:
    error = ValidationError(
        ErrorCode.FILE_NOT_FOUND,
        r"File not found: D:\project\python\secret\missing.docx",
    )

    event = build_error_event(error, run_id="run", operation="read-docx")

    assert "D:\\project\\python\\secret" not in event["message"]
    assert "<path:missing.docx>" in event["message"]
