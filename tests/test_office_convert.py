from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from docrt.config import Config
from docrt.models import ErrorCode
from docrt.office_convert import _run_worker
from docrt.paths import ValidationError


def test_office_worker_failure_carries_structured_context(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "input.xlsx"
    target = tmp_path / "output.pdf"
    source.write_text("x", encoding="utf-8")
    config = Config(work_dir="work")
    result_path = tmp_path / "work" / "run.excel.result.json"

    def fake_run(*_args, **_kwargs):
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            '{"ok": false, "error_message": "excel failed", "detail": "repair prompt"}',
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=1, stdout="worker out", stderr="worker err")

    monkeypatch.setattr("docrt.office_convert.subprocess.run", fake_run)
    monkeypatch.setattr("docrt.office_convert.snapshot_office_processes", lambda: {})
    monkeypatch.setattr("docrt.office_convert.new_office_processes", lambda _before, _after: {})
    monkeypatch.setattr("docrt.office_convert.terminate_processes", lambda _processes: [])

    with pytest.raises(ValidationError) as exc_info:
        _run_worker("excel", source, target, config, "run", timeout=5)

    error = exc_info.value
    assert error.error_code == ErrorCode.EXCEL_CONVERSION_FAILED
    assert error.context["worker_returncode"] == 1
    assert error.context["worker_stdout"] == "worker out"
    assert error.context["worker_stderr"] == "worker err"
    assert error.context["worker_result"]["detail"] == "repair prompt"
    assert error.context["worker_result_json_path"].endswith("run.excel.result.json")


def test_office_worker_timeout_carries_cleanup_context(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "input.docx"
    target = tmp_path / "output.pdf"
    source.write_text("x", encoding="utf-8")
    config = Config(work_dir="work")

    def fake_run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(
            cmd=["office"], timeout=3, output="partial out", stderr="partial err"
        )

    monkeypatch.setattr("docrt.office_convert.subprocess.run", fake_run)
    monkeypatch.setattr("docrt.office_convert.snapshot_office_processes", lambda: {})
    monkeypatch.setattr(
        "docrt.office_convert.new_office_processes",
        lambda _before, _after: {1: object()},
    )
    monkeypatch.setattr("docrt.office_convert.terminate_processes", lambda _processes: ["done"])

    with pytest.raises(ValidationError) as exc_info:
        _run_worker("word", source, target, config, "run", timeout=3)

    error = exc_info.value
    assert error.error_code == ErrorCode.OFFICE_TIMEOUT
    assert error.context["worker_stdout"] == "partial out"
    assert error.context["worker_stderr"] == "partial err"
    assert error.context["created_office_process_count"] == 1
    assert error.context["office_process_cleanup"] == ["done"]
