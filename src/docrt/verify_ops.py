from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docrt.models import ErrorCode
from docrt.paths import ValidationError, validate_input_path
from docrt.read_ops import read_docx, read_xlsx


def verify_docx(
    before_path: str | Path,
    after_path: str | Path,
    expect_path: str | Path | None = None,
) -> dict[str, object]:
    before = read_docx(before_path)
    after = read_docx(after_path)
    result = _compare_docx_read_results(before, after)
    _apply_expectation(result, expect_path)
    return result


def verify_xlsx(
    before_path: str | Path,
    after_path: str | Path,
    expect_path: str | Path | None = None,
) -> dict[str, object]:
    before = read_xlsx(before_path)
    after = read_xlsx(after_path)
    result = _compare_xlsx_read_results(before, after)
    _apply_expectation(result, expect_path)
    return result


def compare_docx(before_path: str | Path, after_path: str | Path) -> dict[str, object]:
    return verify_docx(before_path, after_path)


def compare_xlsx(before_path: str | Path, after_path: str | Path) -> dict[str, object]:
    return verify_xlsx(before_path, after_path)


def _compare_docx_read_results(
    before: dict[str, object], after: dict[str, object]
) -> dict[str, object]:
    before_blocks = _list(before.get("content_blocks"))
    after_blocks = _list(after.get("content_blocks"))
    before_tables = _list(before.get("tables"))
    after_tables = _list(after.get("tables"))
    changed_blocks = _changed_items(before_blocks, after_blocks, "location")
    changed_tables = _changed_tables(before_tables, after_tables)
    changed = bool(changed_blocks or changed_tables)
    return {
        "document_type": "docx",
        "before_path": before.get("path"),
        "after_path": after.get("path"),
        "changed": changed,
        "summary": {
            "before_content_blocks": len(before_blocks),
            "after_content_blocks": len(after_blocks),
            "changed_blocks": len(changed_blocks),
            "before_tables": len(before_tables),
            "after_tables": len(after_tables),
            "changed_tables": len(changed_tables),
        },
        "changed_blocks": changed_blocks,
        "changed_tables": changed_tables,
        "warnings": [*_list(before.get("warnings")), *_list(after.get("warnings"))],
    }


def _compare_xlsx_read_results(
    before: dict[str, object], after: dict[str, object]
) -> dict[str, object]:
    before_blocks = _list(before.get("content_blocks"))
    after_blocks = _list(after.get("content_blocks"))
    before_sheets = {
        str(sheet.get("name")): sheet
        for sheet in _list(_dict(before.get("metadata")).get("sheets"))
        if isinstance(sheet, dict)
    }
    after_sheets = {
        str(sheet.get("name")): sheet
        for sheet in _list(_dict(after.get("metadata")).get("sheets"))
        if isinstance(sheet, dict)
    }
    changed_cells = _changed_items(before_blocks, after_blocks, "location")
    before_names = set(before_sheets)
    after_names = set(after_sheets)
    added_sheets = sorted(after_names - before_names)
    removed_sheets = sorted(before_names - after_names)
    common_sheets = sorted(before_names & after_names)
    changed = bool(changed_cells or added_sheets or removed_sheets)
    return {
        "document_type": "xlsx",
        "before_path": before.get("path"),
        "after_path": after.get("path"),
        "changed": changed,
        "summary": {
            "before_content_blocks": len(before_blocks),
            "after_content_blocks": len(after_blocks),
            "changed_cells": len(changed_cells),
            "added_sheets": len(added_sheets),
            "removed_sheets": len(removed_sheets),
            "common_sheets": len(common_sheets),
        },
        "changed_cells": changed_cells,
        "added_sheets": added_sheets,
        "removed_sheets": removed_sheets,
        "renamed_or_common_sheets": common_sheets,
        "warnings": [*_list(before.get("warnings")), *_list(after.get("warnings"))],
    }


def _changed_items(
    before_items: list[Any], after_items: list[Any], location_key: str
) -> list[dict[str, object]]:
    before_map = {_stable_key(_dict(item).get(location_key)): _dict(item) for item in before_items}
    after_map = {_stable_key(_dict(item).get(location_key)): _dict(item) for item in after_items}
    keys = sorted(set(before_map) | set(after_map))
    changes = []
    for key in keys:
        before = before_map.get(key)
        after = after_map.get(key)
        if before == after:
            continue
        changes.append(
            {
                "location": after.get(location_key) if after else before.get(location_key),
                "before_text": before.get("text") if before else None,
                "after_text": after.get("text") if after else None,
                "change_type": _change_type(before, after),
            }
        )
    return changes


def _changed_tables(before_tables: list[Any], after_tables: list[Any]) -> list[dict[str, object]]:
    max_len = max(len(before_tables), len(after_tables))
    changes = []
    for index in range(max_len):
        before = before_tables[index] if index < len(before_tables) else None
        after = after_tables[index] if index < len(after_tables) else None
        if before == after:
            continue
        changes.append(
            {
                "table_index": index,
                "change_type": _change_type(before, after),
                "before": before,
                "after": after,
            }
        )
    return changes


def _apply_expectation(result: dict[str, object], expect_path: str | Path | None) -> None:
    if expect_path is None:
        return
    patch_file = validate_input_path(expect_path, {".json"})
    try:
        patch = json.loads(patch_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED, f"Expectation JSON is invalid: {exc}"
        ) from exc
    expected_fragments = _expected_fragments(patch)
    missing = []
    result_text = json.dumps(result, ensure_ascii=False)
    for fragment in expected_fragments:
        if fragment not in result_text:
            missing.append(fragment)
    result["expectation"] = {
        "path": str(patch_file),
        "expected_fragments": expected_fragments,
        "missing_fragments": missing,
        "matched": not missing,
    }
    if missing:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED,
            f"Verification did not find expected fragments: {missing}",
        )


def _expected_fragments(patch: Any) -> list[str]:
    if not isinstance(patch, dict):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "Expectation root must be an object")
    operations = patch.get("operations")
    if not isinstance(operations, list):
        return []
    fragments = []
    for operation in operations:
        if not isinstance(operation, dict):
            continue
        for key in ("replace", "text", "value", "new_name", "name"):
            value = operation.get(key)
            if isinstance(value, str):
                fragments.append(value)
    return fragments


def _change_type(before: object, after: object) -> str:
    if before is None:
        return "added"
    if after is None:
        return "removed"
    return "modified"


def _stable_key(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
