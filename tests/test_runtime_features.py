from __future__ import annotations

import json
import os
from pathlib import Path
from time import time

import fitz
import pytest

from docrt.agent import agent_config
from docrt.cache_ops import search
from docrt.config import Config
from docrt.config_cli import config_set
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
        ErrorCode.CORRUPT_DOCUMENT.value,
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
                "operations": [
                    {
                        "type": "replace_heading",
                        "heading_text": "Draft",
                        "text": "Ready",
                    }
                ],
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


def test_schema_validation_accepts_pdf_annotation_task(tmp_path: Path) -> None:
    task_path = tmp_path / "task.json"
    task_path.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "id": "annotate",
                        "task": "annotate-pdf",
                        "input": "sample.pdf",
                        "annotations": "annotations.json",
                        "output": "annotated.pdf",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    assert validate_task(task_path)["valid"] is True


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

    logs_target = next(target for target in report["targets"] if target["name"] == "logs")
    assert any(target["name"] == "state" for target in report["targets"])
    assert logs_target["oldest_file_time"] is not None
    assert planned["dry_run"] is True
    assert planned["planned_count"] == 1
    assert log_path.exists()


def test_clean_all_deduplicates_nested_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work")
    cache_path = tmp_path / "work" / "cache" / "cache.json"
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text("{}", encoding="utf-8")

    planned = clean(config, all_targets=True)

    planned_paths = [item["path"] for item in planned["files"]]
    assert planned_paths.count(str(cache_path)) == 1


def test_clean_retention_uses_configured_target_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(
        outputs_dir="outputs",
        logs_dir="logs",
        work_dir="work",
        diagnostics_dir="outputs/diagnostics",
        log_retention_days=7,
        diagnostic_retention_days=30,
        cache_retention_days=14,
    )
    old_log = tmp_path / "logs" / "old.jsonl"
    fresh_log = tmp_path / "logs" / "fresh.jsonl"
    old_diagnostic = tmp_path / "outputs" / "diagnostics" / "old.json"
    old_cache = tmp_path / "work" / "cache" / "old.json"
    output = tmp_path / "outputs" / "keep.docx"
    for path in [old_log, fresh_log, old_diagnostic, old_cache, output]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    old_mtime = time() - 40 * 24 * 60 * 60
    fresh_mtime = time()
    for path in [old_log, old_diagnostic, old_cache, output]:
        os.utime(path, (old_mtime, old_mtime))
    os.utime(fresh_log, (fresh_mtime, fresh_mtime))

    planned = clean(config, retention=True)

    planned_paths = {item["path"] for item in planned["files"]}
    assert planned["dry_run"] is True
    assert planned["retention"] is True
    assert str(old_log) in planned_paths
    assert str(old_diagnostic) in planned_paths
    assert str(old_cache) in planned_paths
    assert str(fresh_log) not in planned_paths
    assert str(output) not in planned_paths
    assert {item["target"] for item in planned["policy"]} == {
        "logs",
        "diagnostics",
        "cache",
    }


def test_clean_retention_skips_targets_without_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work")
    output = tmp_path / "outputs" / "keep.docx"
    output.parent.mkdir()
    output.write_text("{}", encoding="utf-8")
    old_mtime = time() - 40 * 24 * 60 * 60
    os.utime(output, (old_mtime, old_mtime))

    planned = clean(config, retention=True, outputs=True)

    assert planned["planned_count"] == 0
    assert planned["files"] == []
    assert planned["policy"] == [
        {
            "target": "outputs",
            "older_than_days": None,
            "skipped": True,
            "reason": "no_retention_policy",
        }
    ]


def test_config_set_supports_aliases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = config_set("outputs", "custom-outputs")

    assert result["key"] == "outputs_dir"
    assert Config.load(project_root=tmp_path).outputs_dir == "custom-outputs"


def test_config_set_coerces_retention_aliases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    result = config_set("log_retention", "7")

    assert result["key"] == "log_retention_days"
    assert result["value"] == 7
    assert Config.load(project_root=tmp_path).log_retention_days == 7


def test_agent_config_contains_codex_runtime_fragment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work")

    result = agent_config(config)

    assert result["runtime"]["package"] == "docrt"
    assert result["runtime"]["repository"].endswith("codex-local-doc-runtime.git")
    assert result["runtime"]["primary_entrypoint"] == "uv run docrt"
    assert result["mainline_policy"]["distribution"] == "windows_local_office_runtime_toolchain"
    assert result["mainline_policy"]["auto_installs_uv"] is True
    assert result["mainline_policy"]["default_engine"] == "office_required_native_processing"
    assert result["mainline_policy"]["office_engine"] == "required_local_office_runtime"
    assert result["mainline_policy"]["requires_local_office"] is True
    assert result["mainline_policy"]["standalone_exe_in_main"] is False
    assert result["mainline_policy"]["missing_office_behavior"] == "fail_fast_structured_error"
    assert "uv" in result["environment"]["runtime_required"]
    assert "Microsoft Word desktop COM" in result["environment"]["runtime_required"]
    assert r".\scripts\bootstrap-uv.ps1" in result["environment"]["auto_bootstrap"]
    assert "uv via winget when missing" in result["environment"]["auto_bootstrap"]
    assert result["execution_branches"]["mainline_source_toolchain"]["entrypoint"] == "uv run docrt"
    assert "standalone exe" in result["agents_md"]
    assert ".venv\\Scripts\\docrt.exe" not in result["agents_md"]
    assert "uv run docrt doctor --agent --office-smoke" in result["agents_md"]
    assert r".\scripts\bootstrap-uv.ps1" in result["agents_md"]
    assert "AGENTS.md" in result["agents_md"]
    assert "explain-task" in result["commands"]["task"][1]


def test_search_uses_core_bridge_result_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config = Config(outputs_dir="outputs", logs_dir="logs", work_dir="work")
    index_path = tmp_path / "work" / "index" / "documents.json"
    index_path.parent.mkdir(parents=True)
    index_path.write_text(
        json.dumps({"records": [{"path": "sample.docx", "text": "agent search target"}]}),
        encoding="utf-8",
    )

    result = search("target", config)

    assert result["backend"] in {"python", "rust"}
    assert result["count"] == 1
    assert result["matches"][0]["path"] == "sample.docx"
