from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from docrt.core_bridge import validate_basic_json_object
from docrt.models import ErrorCode
from docrt.paths import ValidationError, validate_input_path

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"


def validate_patch(path: str | Path) -> dict[str, object]:
    data = _load_json_object(path)
    document_type = data.get("document_type")
    if document_type == "docx":
        schema_name = "patch-docx.schema.json"
    elif document_type == "xlsx":
        schema_name = "patch-xlsx.schema.json"
    else:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED,
            "Patch document_type must be 'docx' or 'xlsx'",
        )
    return _validate_data(data, schema_name, path)


def validate_task(path: str | Path) -> dict[str, object]:
    data = _load_json_object(path)
    return _validate_data(data, "task-manifest.schema.json", path)


def validate_result(path: str | Path) -> dict[str, object]:
    data = _load_json_object(path)
    return _validate_data(data, "result.schema.json", path)


def _load_json_object(path: str | Path) -> dict[str, Any]:
    json_path = validate_input_path(path, {".json"})
    text = json_path.read_text(encoding="utf-8")
    validate_basic_json_object(text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"JSON is invalid: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "JSON root must be an object")
    return data


def _validate_data(data: dict[str, Any], schema_name: str, path: str | Path) -> dict[str, object]:
    schema_path = SCHEMA_DIR / schema_name
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda error: list(error.path))
    if errors:
        return {
            "path": str(Path(path).resolve()),
            "schema": str(schema_path),
            "valid": False,
            "errors": [
                {
                    "path": ".".join(str(part) for part in error.path),
                    "message": error.message,
                }
                for error in errors
            ],
        }
    return {
        "path": str(Path(path).resolve()),
        "schema": str(schema_path),
        "valid": True,
        "errors": [],
    }
