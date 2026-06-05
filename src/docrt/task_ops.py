from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docrt.config import Config
from docrt.docx_ops import inspect_docx
from docrt.jsonutil import dump_file
from docrt.models import ErrorCode
from docrt.office_convert import docx_to_pdf, xlsx_to_pdf
from docrt.patch_ops import patch_docx, patch_xlsx
from docrt.paths import (
    ValidationError,
    default_inspect_output,
    default_render_output_dir,
    validate_input_path,
)
from docrt.pdf_ops import inspect_pdf, render_pdf
from docrt.read_ops import read_docx, read_pdf, read_xlsx
from docrt.xlsx_ops import inspect_xlsx

SUPPORTED_TASKS = {
    "inspect-docx",
    "inspect-pdf",
    "inspect-xlsx",
    "read-docx",
    "read-pdf",
    "read-xlsx",
    "patch-docx",
    "patch-xlsx",
    "docx-to-pdf",
    "xlsx-to-pdf",
    "render-pdf",
}


def run_task_manifest(path: str | Path, config: Config, run_id: str) -> dict[str, object]:
    manifest_path = validate_input_path(path, {".json"})
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Task JSON is invalid: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "Task manifest must be an object")
    task = _require_string(manifest, "task")
    if task not in SUPPORTED_TASKS:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Unsupported task: {task}")
    dry_run = bool(manifest.get("dry_run", False))
    if dry_run:
        return {
            "manifest_path": str(manifest_path),
            "dry_run": True,
            "task": task,
            "would_execute": _task_plan(task, manifest),
        }
    return {
        "manifest_path": str(manifest_path),
        "dry_run": False,
        "task": task,
        "result": _execute_task(task, manifest, config, run_id),
    }


def _execute_task(
    task: str, manifest: dict[str, Any], config: Config, run_id: str
) -> dict[str, object]:
    if task == "inspect-docx":
        return _write_optional(inspect_docx(_require_string(manifest, "input")), manifest, config)
    if task == "inspect-pdf":
        return _write_optional(inspect_pdf(_require_string(manifest, "input")), manifest, config)
    if task == "inspect-xlsx":
        return _write_optional(inspect_xlsx(_require_string(manifest, "input")), manifest, config)
    if task == "read-docx":
        return _write_optional(read_docx(_require_string(manifest, "input")), manifest, config)
    if task == "read-pdf":
        return _write_optional(read_pdf(_require_string(manifest, "input")), manifest, config)
    if task == "read-xlsx":
        return _write_optional(read_xlsx(_require_string(manifest, "input")), manifest, config)
    if task == "patch-docx":
        return patch_docx(
            _require_string(manifest, "input"),
            _require_string(manifest, "patch"),
            _require_string(manifest, "output"),
        )
    if task == "patch-xlsx":
        return patch_xlsx(
            _require_string(manifest, "input"),
            _require_string(manifest, "patch"),
            _require_string(manifest, "output"),
        )
    if task == "docx-to-pdf":
        return docx_to_pdf(
            _require_string(manifest, "input"),
            manifest.get("output"),
            config,
            run_id,
        )
    if task == "xlsx-to-pdf":
        return xlsx_to_pdf(
            _require_string(manifest, "input"),
            manifest.get("output"),
            config,
            run_id,
        )
    if task == "render-pdf":
        input_path = Path(_require_string(manifest, "input"))
        output_dir = manifest.get("output_dir") or default_render_output_dir(
            input_path, config.outputs_path
        )
        return render_pdf(input_path, output_dir)
    raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Unsupported task: {task}")


def _write_optional(
    data: dict[str, object], manifest: dict[str, Any], config: Config
) -> dict[str, object]:
    output = manifest.get("output")
    if isinstance(output, str):
        output_path = Path(output)
    else:
        input_path = Path(_require_string(manifest, "input"))
        output_path = default_inspect_output(input_path, config.outputs_path)
    dump_file(output_path, data)
    return {**data, "written_path": str(output_path.resolve())}


def _task_plan(task: str, manifest: dict[str, Any]) -> dict[str, object]:
    plan = {"task": task, "input": manifest.get("input")}
    for key in ("output", "output_dir", "patch"):
        if key in manifest:
            plan[key] = manifest[key]
    return plan


def _require_string(manifest: dict[str, Any], key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"{key} must be a string")
    return value
