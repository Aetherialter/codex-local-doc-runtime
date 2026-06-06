from __future__ import annotations

import json
from pathlib import Path

from docrt.config import Config
from docrt.maintenance import maintenance_report
from docrt.state import read_state, runtime_state, write_state


def test_state_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(state_dir="state")

    path = write_state(config, "sample", {"ok": True})
    loaded = read_state(config, "sample")

    assert path.exists()
    assert loaded is not None
    assert loaded["data"]["ok"] is True


def test_runtime_state_reports_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work", state_dir="state")

    result = runtime_state(config)

    assert result["paths"]["state"] == str((tmp_path / "state").resolve())
    assert result["retention"]["logs_days"] == 14


def test_maintenance_report_writes_state_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work", state_dir="state")
    error_log = tmp_path / "logs" / "errors" / "2026-06-06.error.jsonl"
    error_log.parent.mkdir(parents=True)
    error_log.write_text(
        json.dumps(
            {
                "timestamp": "2026-06-06T00:00:00.000Z",
                "operation": "read-docx",
                "module": "docrt.read_ops",
                "error_code": "FILE_NOT_FOUND",
                "exception_type": "ValidationError",
                "message": "missing file",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = maintenance_report(config, analyze_days=30)

    assert result["log_analysis"]["issue_count"] == 1
    assert result["repair_plan"]["item_count"] == 1
    assert Path(result["state_paths"]["runtime_state"]).exists()
    assert Path(result["state_paths"]["log_analysis"]).exists()
    assert Path(result["state_paths"]["repair_plan"]).exists()
    assert result["recommended_actions"]
