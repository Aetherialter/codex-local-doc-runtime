from __future__ import annotations

import json
from pathlib import Path

from docrt.config import Config
from docrt.errors import build_error_event
from docrt.log_analysis import analyze_logs
from docrt.logging import JsonlLogger
from docrt.models import ErrorCode
from docrt.patch_common import require_string
from docrt.paths import ValidationError
from docrt.repair_plan import repair_plan
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
        (
            r"File not found: D:\project\python\secret\missing.docx; "
            r"original=D:\project\python\secret\missing.docx; "
            r"cwd=D:\project\python\secret; expected_extensions=.docx"
        ),
    )

    event = build_error_event(error, run_id="run", operation="read-docx")

    assert "D:\\project\\python\\secret" not in event["message"]
    assert "<path:missing.docx>" in event["message"]
    assert "expected_extensions=.docx" in event["message"]
    assert "<path:secret; expected_extensions=.docx>" not in event["message"]


def test_error_event_uses_failure_frame_module() -> None:
    try:
        require_string({}, "missing")
    except ValidationError as exc:
        event = build_error_event(exc, run_id="run", operation="validate-patch")

    assert event["module"] == "docrt.patch_common"
    assert event["function"] == "require_string"


def test_repair_plan_prioritizes_and_persists_next_actions(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work", state_dir="state")
    log_path = tmp_path / "logs" / "errors" / "2026-06-06.error.jsonl"
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        "\n".join(
            json.dumps(event)
            for event in [
                {
                    "timestamp": "2026-06-06T00:00:00.000Z",
                    "operation": "docx-to-pdf",
                    "module": "docrt.office_convert",
                    "error_code": "OFFICE_TIMEOUT",
                    "exception_type": "TimeoutExpired",
                    "message": "timeout",
                },
                {
                    "timestamp": "2026-06-06T00:01:00.000Z",
                    "operation": "read-docx",
                    "module": "docrt.paths",
                    "error_code": "FILE_NOT_FOUND",
                    "exception_type": "ValidationError",
                    "message": "missing",
                },
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = repair_plan(config, days=30)

    assert result["item_count"] == 2
    assert result["items"][0]["issue_id"] == "OFFICE_TIMEOUT:docx-to-pdf"
    assert result["items"][0]["priority"] == "P1"
    assert result["items"][0]["requires_confirmation"] is True
    assert Path(str(result["state_path"])).exists()
