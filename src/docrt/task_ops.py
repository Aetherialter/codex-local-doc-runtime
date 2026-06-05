from __future__ import annotations

import json
import re
import traceback as tb
from pathlib import Path
from typing import Any

from docrt.config import Config
from docrt.core_bridge import validate_basic_json_object
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
from docrt.recovery import recovery_actions
from docrt.verify_ops import verify_docx, verify_xlsx
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
    "verify-docx",
    "verify-xlsx",
    "docx-to-pdf",
    "xlsx-to-pdf",
    "render-pdf",
}

STEP_REF_RE = re.compile(r"\$\{steps\.([A-Za-z0-9_-]+)\.([A-Za-z0-9_.-]+)\}")


def run_task_manifest(path: str | Path, config: Config, run_id: str) -> dict[str, object]:
    manifest_path = validate_input_path(path, {".json"})
    text = manifest_path.read_text(encoding="utf-8")
    validate_basic_json_object(text)
    try:
        manifest = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Task JSON is invalid: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "Task manifest must be an object")
    if isinstance(manifest.get("tasks"), list):
        return _run_multi_task_manifest(manifest_path, manifest, config, run_id)
    return _run_single_task_manifest(manifest_path, manifest, config, run_id)


def explain_task_manifest(path: str | Path) -> dict[str, object]:
    manifest_path = validate_input_path(path, {".json"})
    text = manifest_path.read_text(encoding="utf-8")
    validate_basic_json_object(text)
    try:
        manifest = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Task JSON is invalid: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "Task manifest must be an object")
    steps = _manifest_steps(manifest)
    return {
        "manifest_path": str(manifest_path),
        "task_count": len(steps),
        "dry_run": bool(manifest.get("dry_run", False)),
        "reads": _unique(_collect_paths(steps, "reads")),
        "writes": _unique(_collect_paths(steps, "writes")),
        "generates": _unique(_collect_paths(steps, "generates")),
        "patches": _unique(_collect_paths(steps, "patches")),
        "expects": _unique(_collect_paths(steps, "expects")),
        "requires_office_com": any(_requires_office_com(step["task"]) for step in steps),
        "produces_intermediate_artifacts": any(
            step["task"] in {"inspect-docx", "inspect-pdf", "inspect-xlsx", "render-pdf"}
            for step in steps
        ),
        "supports_dry_run": all(_supports_dry_run(step["task"]) for step in steps),
        "steps": steps,
    }


def _run_single_task_manifest(
    manifest_path: Path, manifest: dict[str, Any], config: Config, run_id: str
) -> dict[str, object]:
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


def _run_multi_task_manifest(
    manifest_path: Path, manifest: dict[str, Any], config: Config, run_id: str
) -> dict[str, object]:
    stop_on_error = bool(manifest.get("stop_on_error", True))
    global_dry_run = bool(manifest.get("dry_run", False))
    raw_tasks = manifest["tasks"]
    if not raw_tasks:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "Task manifest tasks must not be empty")
    steps: list[dict[str, object]] = []
    context: dict[str, dict[str, Any]] = {}
    for index, raw_step in enumerate(raw_tasks):
        if not isinstance(raw_step, dict):
            raise ValidationError(
                ErrorCode.VALIDATION_FAILED, f"Task step at index {index} must be an object"
            )
        step_id = _require_string(raw_step, "id")
        task = _require_string(raw_step, "task")
        if step_id in context:
            raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Duplicate task step id: {step_id}")
        if task not in SUPPORTED_TASKS:
            raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Unsupported task: {task}")
        resolved_step = _resolve_refs(raw_step, context)
        dry_run = global_dry_run or bool(resolved_step.get("dry_run", False))
        if dry_run:
            step_result = {
                "id": step_id,
                "task": task,
                "ok": True,
                "dry_run": True,
                "result": {"would_execute": _task_plan(task, resolved_step)},
            }
        else:
            step_result = _run_step(step_id, task, resolved_step, config, f"{run_id}-{step_id}")
        steps.append(step_result)
        context[step_id] = _flatten_step_context(step_result)
        if stop_on_error and not step_result["ok"]:
            break
    failed_count = sum(1 for step in steps if not step["ok"])
    return {
        "manifest_path": str(manifest_path),
        "dry_run": global_dry_run,
        "stop_on_error": stop_on_error,
        "success_count": len(steps) - failed_count,
        "failed_count": failed_count,
        "steps": steps,
    }


def _run_step(
    step_id: str,
    task: str,
    manifest: dict[str, Any],
    config: Config,
    run_id: str,
) -> dict[str, object]:
    try:
        result = _execute_task(task, manifest, config, run_id)
    except Exception as exc:
        error_code = _classify(exc).value
        error = {
            "error_code": error_code,
            "error_message": str(exc),
            "exception_type": type(exc).__name__,
            "traceback": tb.format_exc(),
            "recovery_actions": recovery_actions(error_code),
        }
        return {
            "id": step_id,
            "task": task,
            "ok": False,
            "error": error,
            **error,
        }
    return {
        "id": step_id,
        "task": task,
        "ok": True,
        "result": result,
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
            dry_run=bool(manifest.get("dry_run", False)),
        )
    if task == "patch-xlsx":
        return patch_xlsx(
            _require_string(manifest, "input"),
            _require_string(manifest, "patch"),
            _require_string(manifest, "output"),
            dry_run=bool(manifest.get("dry_run", False)),
        )
    if task == "verify-docx":
        return verify_docx(
            _require_string(manifest, "before"),
            _require_string(manifest, "after"),
            manifest.get("expect"),
        )
    if task == "verify-xlsx":
        return verify_xlsx(
            _require_string(manifest, "before"),
            _require_string(manifest, "after"),
            manifest.get("expect"),
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
    plan = {"task": task}
    for key in (
        "input",
        "before",
        "after",
        "output",
        "output_dir",
        "patch",
        "expect",
        "dry_run",
    ):
        if key in manifest:
            plan[key] = manifest[key]
    return plan


def _manifest_steps(manifest: dict[str, Any]) -> list[dict[str, object]]:
    if isinstance(manifest.get("tasks"), list):
        steps = []
        context: dict[str, dict[str, Any]] = {}
        for index, raw_step in enumerate(manifest["tasks"]):
            if not isinstance(raw_step, dict):
                raise ValidationError(
                    ErrorCode.VALIDATION_FAILED, f"Task step at index {index} must be an object"
                )
            task = _require_string(raw_step, "task")
            if task not in SUPPORTED_TASKS:
                raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Unsupported task: {task}")
            resolved_step = _resolve_refs(raw_step, context)
            step = _explain_step(resolved_step, index=index)
            steps.append(step)
            step_id = raw_step.get("id")
            if isinstance(step_id, str):
                context[step_id] = _explain_step_context(step)
        return steps
    task = _require_string(manifest, "task")
    if task not in SUPPORTED_TASKS:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Unsupported task: {task}")
    return [_explain_step(manifest, index=0)]


def _explain_step(manifest: dict[str, Any], *, index: int) -> dict[str, object]:
    task = _require_string(manifest, "task")
    reads: list[str] = []
    writes: list[str] = []
    generates: list[str] = []
    patches: list[str] = []
    expects: list[str] = []
    if "input" in manifest:
        reads.append(str(manifest["input"]))
    if "before" in manifest:
        reads.append(str(manifest["before"]))
    if "after" in manifest:
        reads.append(str(manifest["after"]))
    if "patch" in manifest:
        patches.append(str(manifest["patch"]))
        reads.append(str(manifest["patch"]))
    if "expect" in manifest:
        expects.append(str(manifest["expect"]))
        reads.append(str(manifest["expect"]))
    if "output" in manifest:
        output = str(manifest["output"])
        writes.append(output)
        generates.append(output)
    if "output_dir" in manifest:
        output_dir = str(manifest["output_dir"])
        writes.append(output_dir)
        generates.append(output_dir)
    return {
        "index": index,
        "id": manifest.get("id"),
        "task": task,
        "reads": _unique(reads),
        "writes": _unique(writes),
        "generates": _unique(generates),
        "patches": _unique(patches),
        "expects": _unique(expects),
        "requires_office_com": _requires_office_com(task),
        "supports_dry_run": _supports_dry_run(task),
        "supports_native_dry_run": task in {"patch-docx", "patch-xlsx"},
        "dry_run": bool(manifest.get("dry_run", False)),
    }


def _collect_paths(steps: list[dict[str, object]], key: str) -> list[str]:
    paths: list[str] = []
    for step in steps:
        value = step.get(key, [])
        if isinstance(value, list):
            paths.extend(str(item) for item in value)
    return paths


def _requires_office_com(task: str) -> bool:
    return task in {"docx-to-pdf", "xlsx-to-pdf"}


def _supports_dry_run(task: str) -> bool:
    return task in SUPPORTED_TASKS


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _explain_step_context(step: dict[str, object]) -> dict[str, Any]:
    context: dict[str, Any] = dict(step)
    writes = step.get("writes")
    generates = step.get("generates")
    if isinstance(writes, list) and writes:
        context["output_path"] = writes[0]
    if isinstance(generates, list) and generates:
        context["generated_path"] = generates[0]
    return context


def _resolve_refs(value: Any, context: dict[str, dict[str, Any]]) -> Any:
    if isinstance(value, str):
        return STEP_REF_RE.sub(lambda match: str(_lookup_ref(match, context)), value)
    if isinstance(value, dict):
        return {key: _resolve_refs(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_refs(item, context) for item in value]
    return value


def _lookup_ref(match: re.Match[str], context: dict[str, dict[str, Any]]) -> object:
    step_id = match.group(1)
    path = match.group(2)
    if step_id not in context:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Unknown step reference: {step_id}")
    value: Any = context[step_id]
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            raise ValidationError(
                ErrorCode.VALIDATION_FAILED,
                f"Unknown step reference field: steps.{step_id}.{path}",
            )
    return value


def _flatten_step_context(step: dict[str, object]) -> dict[str, Any]:
    context: dict[str, Any] = dict(step)
    result = step.get("result")
    if isinstance(result, dict):
        context.update(result)
    return context


def _classify(exc: Exception) -> ErrorCode:
    if isinstance(exc, ValidationError):
        return exc.error_code
    return ErrorCode.UNKNOWN_ERROR


def _require_string(manifest: dict[str, Any], key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"{key} must be a string")
    return value
