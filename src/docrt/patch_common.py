from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docrt.core_bridge import validate_basic_json_object
from docrt.models import ErrorCode
from docrt.paths import ValidationError


def load_patch(path: Path, *, expected_document_type: str) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    validate_basic_json_object(text)
    try:
        patch = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Patch JSON is invalid: {exc}") from exc
    document_type = patch.get("document_type")
    if document_type != expected_document_type:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED,
            f"Patch document_type must be {expected_document_type!r}",
        )
    operations = patch.get("operations")
    if not isinstance(operations, list) or not operations:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED, "Patch operations must be a non-empty list"
        )
    for index, operation in enumerate(operations):
        if not isinstance(operation, dict) or not isinstance(operation.get("type"), str):
            raise ValidationError(
                ErrorCode.VALIDATION_FAILED,
                f"Patch operation at index {index} must be an object with a string type",
            )
    return patch


def ensure_distinct_output(source: Path, target: Path) -> None:
    if source == target:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED,
            "Patch commands require an output path different from the input path",
        )


def patch_summary(
    changes: list[dict[str, object]],
    skipped_count: int,
    conflicts: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "operation_count": len(changes),
        "planned_count": sum(int(change.get("planned_count", 1)) for change in changes),
        "applied_count": sum(int(change.get("applied_count", 1)) for change in changes),
        "skipped_count": skipped_count,
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "planned_changes": changes,
        "changes": changes,
    }


def verification_summary(verification: dict[str, object] | None) -> dict[str, object] | None:
    if verification is None:
        return None
    return {
        "document_type": verification["document_type"],
        "content_blocks": len(verification["content_blocks"]),
        "tables": len(verification["tables"]),
        "warnings": verification["warnings"],
    }


def require_string(operation: dict[str, Any], key: str) -> str:
    value = operation.get(key)
    if not isinstance(value, str):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"{key} must be a string")
    return value


def require_int(operation: dict[str, Any], key: str) -> int:
    value = operation.get(key)
    if not isinstance(value, int):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"{key} must be an integer")
    return value
