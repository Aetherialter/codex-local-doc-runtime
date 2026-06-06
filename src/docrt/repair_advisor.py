from __future__ import annotations

from typing import Any

REPAIR_RULES: dict[str, dict[str, object]] = {
    "FILE_NOT_FOUND": {
        "severity": "medium",
        "risk": "low",
        "likely_cause": "Input paths are missing, relative to an unexpected cwd, or moved.",
        "summary": "Improve path validation guidance and prefer absolute paths in task manifests.",
        "files": ["src/docrt/paths.py", "src/docrt/task_ops.py", "README.md"],
        "validation": ["uv run pytest tests\\test_config_paths.py", "uv run ruff check ."],
    },
    "FILE_LOCKED": {
        "severity": "medium",
        "risk": "low",
        "likely_cause": "Word, Excel, a PDF viewer, or a sync tool is holding the file.",
        "summary": (
            "Surface lock-specific recovery guidance and suggest writing to a new output path."
        ),
        "files": ["src/docrt/paths.py", "src/docrt/recovery.py"],
        "validation": ["uv run pytest tests\\test_config_paths.py", "uv run ruff check ."],
    },
    "VALIDATION_FAILED": {
        "severity": "medium",
        "risk": "medium",
        "likely_cause": (
            "Patch, task manifest, expected text, or operation fields do not match protocol."
        ),
        "summary": (
            "Add preflight checks and clearer schema-level diagnostics before applying changes."
        ),
        "files": [
            "src/docrt/schema_ops.py",
            "src/docrt/task_ops.py",
            "src/docrt/patch_ops.py",
            "schemas/",
        ],
        "validation": [
            "uv run pytest tests\\test_read_patch_verify_task.py",
            "uv run pytest tests\\test_runtime_features.py",
            "uv run ruff check .",
        ],
    },
    "PATH_VALIDATION_FAILED": {
        "severity": "medium",
        "risk": "low",
        "likely_cause": (
            "A configured runtime directory or requested output path is outside the project root."
        ),
        "summary": (
            "Validate configured directories and document safe cleanup/output path boundaries."
        ),
        "files": [
            "src/docrt/storage_ops.py",
            "src/docrt/paths.py",
            "src/docrt/config.py",
            "docs/storage-management.md",
        ],
        "validation": [
            "uv run pytest tests\\test_config_paths.py tests\\test_runtime_features.py",
            "uv run ruff check .",
        ],
    },
    "OFFICE_TIMEOUT": {
        "severity": "high",
        "risk": "medium",
        "likely_cause": (
            "Office COM conversion is blocked by a large document, dialog, or process lock."
        ),
        "summary": (
            "Improve Office timeout diagnostics and recommend background job mode for conversion."
        ),
        "files": ["src/docrt/office_convert.py", "src/docrt/doctor.py"],
        "validation": ["uv run pytest tests\\test_doctor.py", "uv run ruff check ."],
    },
    "WORD_CONVERSION_FAILED": {
        "severity": "high",
        "risk": "medium",
        "likely_cause": (
            "Word failed to open or export the document, often because of repair prompts."
        ),
        "summary": (
            "Record worker stderr/stdout and add a preflight Office smoke check before conversion."
        ),
        "files": ["src/docrt/office_convert.py", "src/docrt/office_worker.py"],
        "validation": ["uv run pytest", "uv run ruff check ."],
    },
    "EXCEL_CONVERSION_FAILED": {
        "severity": "high",
        "risk": "medium",
        "likely_cause": (
            "Excel failed to open or export the workbook, often because of repair prompts."
        ),
        "summary": (
            "Record worker stderr/stdout and add a preflight Office smoke check before conversion."
        ),
        "files": ["src/docrt/office_convert.py", "src/docrt/office_worker.py"],
        "validation": ["uv run pytest", "uv run ruff check ."],
    },
    "UNKNOWN_ERROR": {
        "severity": "high",
        "risk": "medium",
        "likely_cause": "An exception escaped without a specific ErrorCode classification.",
        "summary": "Add targeted exception classification at the failing module boundary.",
        "files": ["src/docrt/runner.py", "src/docrt/errors.py"],
        "validation": ["uv run pytest", "uv run ruff check ."],
    },
}


def recommendations_for_issue(issue: dict[str, Any]) -> list[dict[str, object]]:
    error_code = str(issue.get("error_code") or "UNKNOWN_ERROR")
    rule = REPAIR_RULES.get(error_code, REPAIR_RULES["UNKNOWN_ERROR"])
    operation = issue.get("operation")
    operations = issue.get("operations")
    modules = issue.get("modules")
    count = int(issue.get("count", 0))
    severity = str(rule["severity"])
    if count >= 5 and severity == "medium":
        severity = "high"
    return [
        {
            "issue_id": issue.get("issue_id"),
            "severity": severity,
            "risk": rule["risk"],
            "count": count,
            "affected_operations": operations
            if isinstance(operations, list)
            else ([operation] if isinstance(operation, str) else []),
            "affected_modules": modules if isinstance(modules, list) else [],
            "likely_cause": rule["likely_cause"],
            "suggested_fix": {
                "summary": rule["summary"],
                "files": rule["files"],
                "validation": rule["validation"],
            },
            "requires_confirmation": rule["risk"] in {"medium", "high"},
        }
    ]
