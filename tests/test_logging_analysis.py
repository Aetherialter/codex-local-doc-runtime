from __future__ import annotations

import json
from pathlib import Path

from docrt.config import Config
from docrt.errors import build_error_event, classify_exception
from docrt.log_analysis import analyze_logs
from docrt.logging import JsonlLogger
from docrt.models import ErrorCode
from docrt.patch_common import require_string
from docrt.paths import ValidationError, validate_input_path
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


def test_run_operation_preserves_missing_file_path_resolution(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work")

    def fail(_run_id, _config, _logger):
        validate_input_path("missing.docx", {".docx"})

    result = run_operation("read-docx", fail, config=config, backend="python")

    assert result.ok is False
    error_log = next((tmp_path / "logs" / "errors").glob("*.error.jsonl"))
    event = json.loads(error_log.read_text(encoding="utf-8").splitlines()[0])
    resolution = event["context"]["path_resolution"]
    assert resolution["input"]["name"] == "missing.docx"
    assert resolution["resolved_path"]["name"] == "missing.docx"
    assert resolution["exists"] is False
    assert event["context"]["expected_extensions"] == [".docx"]


def test_error_event_includes_validation_error_context() -> None:
    error = ValidationError(
        ErrorCode.EXCEL_CONVERSION_FAILED,
        "excel failed",
        context={
            "input_path": r"D:\project\python\secret\input.xlsx",
            "worker_returncode": 1,
            "worker_stderr": "COM repair prompt",
        },
    )

    event = build_error_event(error, run_id="run", operation="xlsx-to-pdf")

    assert event["context"]["input_path"]["name"] == "input.xlsx"
    assert event["context"]["worker_returncode"] == 1
    assert event["context"]["worker_stderr"] == "COM repair prompt"


def test_classify_exception_maps_common_runtime_failures() -> None:
    assert classify_exception(ModuleNotFoundError("docx")) == ErrorCode.DEPENDENCY_MISSING
    assert classify_exception(FileNotFoundError("missing")) == ErrorCode.FILE_NOT_FOUND
    assert classify_exception(PermissionError("denied")) == ErrorCode.PERMISSION_DENIED
    assert (
        classify_exception(RuntimeError("PyMuPDF is unavailable")) == ErrorCode.DEPENDENCY_MISSING
    )
    assert classify_exception(ValueError("bad value")) == ErrorCode.VALIDATION_FAILED


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


def test_analyze_logs_marks_issue_recovered_after_later_success(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work")
    error_log = tmp_path / "logs" / "errors" / "2026-06-06.error.jsonl"
    success_log = tmp_path / "logs" / "success.jsonl"
    error_log.parent.mkdir(parents=True)
    error_log.write_text(
        json.dumps(
            {
                "timestamp": "2026-06-06T00:00:00.000Z",
                "operation": "xlsx-to-pdf",
                "module": "excel-com",
                "error_code": "EXCEL_CONVERSION_FAILED",
                "exception_type": "ValidationError",
                "message": "excel failed",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    success_log.write_text(
        json.dumps(
            {
                "run_id": "success",
                "operation": "xlsx-to-pdf",
                "event": "finished",
                "result": {
                    "ok": True,
                    "operation": "xlsx-to-pdf",
                    "backend": "excel-com",
                    "run_id": "success",
                    "ended_at": "2026-06-06T00:10:00.000Z",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = analyze_logs(config, days=30)
    issue = result["issues"][0]

    assert result["scanned_success_events"] == 1
    assert issue["issue_id"] == "EXCEL_CONVERSION_FAILED:xlsx-to-pdf"
    assert issue["status"] == "observed_recovered"
    assert issue["success_after_last_error"] is True
    assert issue["last_success_at"] == "2026-06-06T00:10:00.000Z"


def test_analyze_logs_reads_legacy_run_log_failure_results(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work")
    run_log = tmp_path / "logs" / "legacy.jsonl"
    run_log.parent.mkdir(parents=True)
    run_log.write_text(
        json.dumps(
            {
                "run_id": "legacy",
                "operation": "read-docx",
                "event": "finished",
                "result": {
                    "ok": False,
                    "operation": "read-docx",
                    "run_id": "legacy",
                    "ended_at": "2026-06-06T00:00:00.000Z",
                    "input_path": r"D:\project\python\secret\missing.docx",
                    "output_path": None,
                    "backend": "python-docx",
                    "error_code": "FILE_NOT_FOUND",
                    "error_message": r"File not found: D:\project\python\secret\missing.docx",
                    "exception_type": "ValidationError",
                    "traceback": r"Traceback D:\project\python\secret\missing.docx",
                    "recovery_actions": ["check path"],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = analyze_logs(config, days=30, include_events=True)

    assert result["scanned_error_events"] == 1
    assert result["issues"][0]["issue_id"] == "FILE_NOT_FOUND:read-docx"
    event = result["events"][0]
    assert "D:\\project\\python\\secret" not in event["message"]
    assert event["context"]["input_path"]["name"] == "missing.docx"


def test_analyze_logs_deduplicates_error_and_run_log_events(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work")
    error_event = {
        "schema_version": "1.0",
        "event_id": "run-error",
        "run_id": "run",
        "timestamp": "2026-06-06T00:00:00.000Z",
        "level": "error",
        "operation": "read-docx",
        "module": "docrt.paths",
        "function": "validate_input_path",
        "error_code": "FILE_NOT_FOUND",
        "exception_type": "ValidationError",
        "message": "missing",
    }
    error_log = tmp_path / "logs" / "errors" / "2026-06-06.error.jsonl"
    run_log = tmp_path / "logs" / "run.jsonl"
    error_log.parent.mkdir(parents=True)
    error_log.write_text(json.dumps(error_event) + "\n", encoding="utf-8")
    run_log.write_text(
        json.dumps(
            {
                "run_id": "run",
                "operation": "read-docx",
                "event": "finished",
                "result": {
                    "ok": False,
                    "operation": "read-docx",
                    "run_id": "run",
                    "ended_at": "2026-06-06T00:00:00.000Z",
                    "backend": "python",
                    "error_code": "FILE_NOT_FOUND",
                    "error_message": "missing",
                    "exception_type": "ValidationError",
                    "traceback": "",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = analyze_logs(config, days=30)

    assert result["scanned_error_events"] == 1
    assert result["issues"][0]["count"] == 1


def test_path_validation_repair_advice_targets_path_boundaries(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work")
    log_path = tmp_path / "logs" / "errors" / "2026-06-06.error.jsonl"
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        json.dumps(
            {
                "timestamp": "2026-06-06T00:00:00.000Z",
                "operation": "clean",
                "module": "docrt.storage_ops",
                "error_code": "PATH_VALIDATION_FAILED",
                "exception_type": "ValidationError",
                "message": "outside project root",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = analyze_logs(config, days=30)
    recommendation = result["recommendations"][0]

    assert recommendation["issue_id"] == "PATH_VALIDATION_FAILED:clean"
    assert recommendation["risk"] == "low"
    assert "src/docrt/storage_ops.py" in recommendation["suggested_fix"]["files"]


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


def test_repair_plan_demotes_recovered_issues(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work", state_dir="state")
    error_log = tmp_path / "logs" / "errors" / "2026-06-06.error.jsonl"
    error_log.parent.mkdir(parents=True)
    error_log.write_text(
        "\n".join(
            json.dumps(event)
            for event in [
                {
                    "timestamp": "2026-06-06T00:00:00.000Z",
                    "operation": "xlsx-to-pdf",
                    "module": "excel-com",
                    "error_code": "EXCEL_CONVERSION_FAILED",
                    "exception_type": "ValidationError",
                    "message": "excel failed",
                },
                {
                    "timestamp": "2026-06-06T00:30:00.000Z",
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
    (tmp_path / "logs" / "success.jsonl").write_text(
        json.dumps(
            {
                "run_id": "success",
                "operation": "xlsx-to-pdf",
                "event": "finished",
                "result": {
                    "ok": True,
                    "operation": "xlsx-to-pdf",
                    "backend": "excel-com",
                    "run_id": "success",
                    "ended_at": "2026-06-06T00:10:00.000Z",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = repair_plan(config, days=30)

    assert result["items"][0]["issue_id"] == "FILE_NOT_FOUND:read-docx"
    assert result["items"][1]["issue_id"] == "EXCEL_CONVERSION_FAILED:xlsx-to-pdf"
    assert result["items"][1]["priority"] == "P4"
    assert result["items"][1]["status"] == "observed_recovered"
    assert result["items"][1]["auto_apply_allowed"] is False
    assert "successful run" in str(result["items"][1]["next_step"])


def test_repair_plan_treats_unsupported_boundaries_as_monitoring(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work", state_dir="state")
    error_log = tmp_path / "logs" / "errors" / "2026-06-06.error.jsonl"
    error_log.parent.mkdir(parents=True)
    error_log.write_text(
        "\n".join(
            json.dumps(event)
            for event in [
                {
                    "timestamp": "2026-06-06T00:00:00.000Z",
                    "operation": "read-docx",
                    "module": "docrt.paths",
                    "error_code": "UNSUPPORTED_LEGACY_FORMAT",
                    "exception_type": "ValidationError",
                    "message": "legacy format",
                },
                {
                    "timestamp": "2026-06-06T00:01:00.000Z",
                    "operation": "read-docx",
                    "module": "docrt.paths",
                    "error_code": "ENCRYPTED_FILE_UNSUPPORTED",
                    "exception_type": "ValidationError",
                    "message": "encrypted file",
                },
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = repair_plan(config, days=30)

    assert result["item_count"] == 2
    assert {item["priority"] for item in result["items"]} == {"P4"}
    assert {item["category"] for item in result["items"]} == {"unsupported_boundary"}
    assert {item["status"] for item in result["items"]} == {"unsupported_boundary"}
    assert result["summary"]["auto_apply_allowed"] == 0
    assert all(
        "documented v1.1 unsupported boundary" in str(item["next_step"]) for item in result["items"]
    )
