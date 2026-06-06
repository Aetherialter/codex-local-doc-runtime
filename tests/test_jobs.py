from __future__ import annotations

import json
import time
from pathlib import Path

from docrt.config import Config
from docrt.jobs import job_status, start_job
from docrt.log_analysis import analyze_logs


def test_start_job_rejects_unsupported_task(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(state_dir="state")

    result = start_job(config, "render-pdf")

    assert result["started"] is False
    assert "maintenance" in result["supported_tasks"]
    assert "clean-retention" in result["supported_tasks"]


def test_start_job_runs_maintenance_and_writes_status(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(
        outputs_dir="outputs",
        logs_dir="logs",
        work_dir="work",
        diagnostics_dir="outputs/diagnostics",
        state_dir="state",
    )

    started = start_job(config, "maintenance", args=["--days", "30"])
    job_id = str(started["job_id"])

    assert started["started"] is True
    final = _wait_for_job(config, job_id)
    assert final["found"] is True
    assert final["job"]["status"] == "succeeded"
    assert Path(final["job"]["result_path"]).exists()


def test_start_job_runs_repair_plan_and_writes_status(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work", state_dir="state")

    started = start_job(config, "repair-plan", args=["--days", "30"])
    job_id = str(started["job_id"])
    final = _wait_for_job(config, job_id)

    assert final["job"]["status"] == "succeeded"
    assert Path(final["job"]["result_path"]).exists()


def test_start_job_runs_clean_retention_as_dry_run(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(
        outputs_dir="outputs",
        logs_dir="logs",
        work_dir="work",
        diagnostics_dir="outputs/diagnostics",
        state_dir="state",
    )
    log_path = tmp_path / "logs" / "old.jsonl"
    log_path.parent.mkdir()
    log_path.write_text("{}", encoding="utf-8")

    started = start_job(config, "clean-retention")
    job_id = str(started["job_id"])
    final = _wait_for_job(config, job_id)
    result_path = Path(final["job"]["result_path"])

    assert final["job"]["status"] == "succeeded"
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["data"]["retention"] is True
    assert payload["data"]["dry_run"] is True
    assert log_path.exists()


def test_background_job_failure_writes_error_log_and_diagnostic(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docrt.config.json").write_text(
        json.dumps({"logs_dir": "../outside-logs"}), encoding="utf-8"
    )
    config = Config(
        outputs_dir="outputs",
        logs_dir="logs",
        work_dir="work",
        diagnostics_dir="outputs/diagnostics",
        state_dir="state",
    )

    started = start_job(config, "clean-retention")
    job_id = str(started["job_id"])
    final = _wait_for_job(config, job_id)
    result_path = Path(final["job"]["result_path"])
    payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert final["job"]["status"] == "failed"
    assert final["job"]["error_code"] == "PATH_VALIDATION_FAILED"
    assert payload["ok"] is False
    assert payload["diagnostic_report_path"]
    assert Path(str(payload["diagnostic_report_path"])).exists()

    error_logs = list((tmp_path.parent / "outside-logs" / "errors").glob("*.error.jsonl"))
    assert len(error_logs) == 1
    event = json.loads(error_logs[0].read_text(encoding="utf-8").splitlines()[0])
    assert event["operation"] == "job:clean-retention"
    assert event["error_code"] == "PATH_VALIDATION_FAILED"
    assert event["context"]["task"] == "clean-retention"
    assert "status_path" in event["context"]

    analysis = analyze_logs(Config(logs_dir="../outside-logs"), days=30)
    assert analysis["issues"][0]["issue_id"] == "PATH_VALIDATION_FAILED:job:clean-retention"


def _wait_for_job(config: Config, job_id: str) -> dict[str, object]:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        status = job_status(config, job_id)
        if status.get("found") and status["job"].get("status") in {"succeeded", "failed"}:
            return status
        time.sleep(0.1)
    return job_status(config, job_id)
