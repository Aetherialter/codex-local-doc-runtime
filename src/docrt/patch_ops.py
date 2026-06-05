from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from docrt.models import ErrorCode
from docrt.paths import (
    ValidationError,
    ensure_output_not_locked,
    ensure_unlocked_for_read,
    validate_input_path,
    validate_output_path,
)
from docrt.read_ops import read_docx, read_xlsx


def patch_docx(
    input_path: str | Path, patch_path: str | Path, output_path: str | Path
) -> dict[str, object]:
    source = validate_input_path(input_path, {".docx"})
    patch_file = validate_input_path(patch_path, {".json"})
    target = validate_output_path(output_path)
    _ensure_distinct_output(source, target)
    ensure_unlocked_for_read(source)
    ensure_unlocked_for_read(patch_file)
    ensure_output_not_locked(target)
    patch = _load_patch(patch_file, expected_document_type="docx")

    shutil.copyfile(source, target)
    try:
        from docx import Document
    except Exception as exc:
        raise RuntimeError("python-docx is unavailable") from exc

    document = Document(str(target))
    changes: list[dict[str, object]] = []
    for operation in patch["operations"]:
        op_type = operation.get("type")
        if op_type == "replace_text":
            changes.append(_docx_replace_text(document, operation))
        elif op_type == "replace_paragraph":
            changes.append(_docx_replace_paragraph(document, operation))
        elif op_type == "replace_table_cell":
            changes.append(_docx_replace_table_cell(document, operation))
        else:
            raise ValidationError(
                ErrorCode.VALIDATION_FAILED, f"Unsupported DOCX patch op: {op_type}"
            )
    document.save(str(target))
    verification = read_docx(target)
    return {
        "input_path": str(source),
        "patch_path": str(patch_file),
        "output_path": str(target),
        "patch_summary": {"operation_count": len(changes), "changes": changes},
        "verification": {
            "document_type": verification["document_type"],
            "content_blocks": len(verification["content_blocks"]),
            "tables": len(verification["tables"]),
            "warnings": verification["warnings"],
        },
    }


def patch_xlsx(
    input_path: str | Path, patch_path: str | Path, output_path: str | Path
) -> dict[str, object]:
    source = validate_input_path(input_path, {".xlsx"})
    patch_file = validate_input_path(patch_path, {".json"})
    target = validate_output_path(output_path)
    _ensure_distinct_output(source, target)
    ensure_unlocked_for_read(source)
    ensure_unlocked_for_read(patch_file)
    ensure_output_not_locked(target)
    patch = _load_patch(patch_file, expected_document_type="xlsx")

    shutil.copyfile(source, target)
    try:
        import openpyxl
    except Exception as exc:
        raise RuntimeError("openpyxl is unavailable") from exc

    workbook = openpyxl.load_workbook(str(target))
    changes: list[dict[str, object]] = []
    try:
        for operation in patch["operations"]:
            op_type = operation.get("type")
            if op_type == "set_cell":
                changes.append(_xlsx_set_cell(workbook, operation))
            elif op_type == "set_range_values":
                changes.extend(_xlsx_set_range_values(workbook, operation))
            elif op_type == "add_sheet":
                changes.append(_xlsx_add_sheet(workbook, operation))
            elif op_type == "rename_sheet":
                changes.append(_xlsx_rename_sheet(workbook, operation))
            else:
                raise ValidationError(
                    ErrorCode.VALIDATION_FAILED,
                    f"Unsupported XLSX patch op: {op_type}",
                )
        workbook.save(str(target))
    finally:
        workbook.close()

    verification = read_xlsx(target)
    return {
        "input_path": str(source),
        "patch_path": str(patch_file),
        "output_path": str(target),
        "patch_summary": {"operation_count": len(changes), "changes": changes},
        "verification": {
            "document_type": verification["document_type"],
            "content_blocks": len(verification["content_blocks"]),
            "tables": len(verification["tables"]),
            "warnings": verification["warnings"],
        },
    }


def _load_patch(path: Path, *, expected_document_type: str) -> dict[str, Any]:
    try:
        patch = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Patch JSON is invalid: {exc}") from exc
    if not isinstance(patch, dict):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "Patch root must be an object")
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


def _ensure_distinct_output(source: Path, target: Path) -> None:
    if source == target:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED,
            "Patch commands require an output path different from the input path",
        )


def _docx_replace_text(document, operation: dict[str, Any]) -> dict[str, object]:
    find = _require_string(operation, "find")
    replace = _require_string(operation, "replace")
    count = 0
    for paragraph in document.paragraphs:
        if find in paragraph.text:
            paragraph.text = paragraph.text.replace(find, replace)
            count += 1
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                if find in cell.text:
                    cell.text = cell.text.replace(find, replace)
                    count += 1
    return {"type": "replace_text", "find": find, "replace": replace, "matches": count}


def _docx_replace_paragraph(document, operation: dict[str, Any]) -> dict[str, object]:
    index = _require_int(operation, "paragraph_index")
    text = _require_string(operation, "text")
    try:
        old_text = document.paragraphs[index].text
    except IndexError as exc:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED, f"Paragraph index out of range: {index}"
        ) from exc
    document.paragraphs[index].text = text
    return {
        "type": "replace_paragraph",
        "paragraph_index": index,
        "old_text": old_text,
        "text": text,
    }


def _docx_replace_table_cell(document, operation: dict[str, Any]) -> dict[str, object]:
    table_index = _require_int(operation, "table_index")
    row_index = _require_int(operation, "row_index")
    column_index = _require_int(operation, "column_index")
    text = _require_string(operation, "text")
    try:
        cell = document.tables[table_index].rows[row_index].cells[column_index]
    except IndexError as exc:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED,
            f"Table cell location out of range: {table_index}/{row_index}/{column_index}",
        ) from exc
    old_text = cell.text
    cell.text = text
    return {
        "type": "replace_table_cell",
        "table_index": table_index,
        "row_index": row_index,
        "column_index": column_index,
        "old_text": old_text,
        "text": text,
    }


def _xlsx_set_cell(workbook, operation: dict[str, Any]) -> dict[str, object]:
    sheet = _worksheet(workbook, _require_string(operation, "sheet"))
    cell = _require_string(operation, "cell")
    value = operation.get("value")
    old_value = sheet[cell].value
    sheet[cell] = value
    return {
        "type": "set_cell",
        "sheet": sheet.title,
        "cell": cell,
        "old_value": old_value,
        "value": value,
    }


def _xlsx_set_range_values(workbook, operation: dict[str, Any]) -> list[dict[str, object]]:
    sheet = _worksheet(workbook, _require_string(operation, "sheet"))
    start_cell = _require_string(operation, "start_cell")
    values = operation.get("values")
    if (
        not isinstance(values, list)
        or not values
        or not all(isinstance(row, list) for row in values)
    ):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "values must be a non-empty 2D list")
    start = sheet[start_cell]
    changes = []
    for row_offset, row_values in enumerate(values):
        for column_offset, value in enumerate(row_values):
            cell = sheet.cell(start.row + row_offset, start.column + column_offset)
            old_value = cell.value
            cell.value = value
            changes.append(
                {
                    "type": "set_cell",
                    "sheet": sheet.title,
                    "cell": cell.coordinate,
                    "old_value": old_value,
                    "value": value,
                }
            )
    return changes


def _xlsx_add_sheet(workbook, operation: dict[str, Any]) -> dict[str, object]:
    name = _require_string(operation, "name")
    if name in workbook.sheetnames:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Sheet already exists: {name}")
    workbook.create_sheet(name)
    return {"type": "add_sheet", "name": name}


def _xlsx_rename_sheet(workbook, operation: dict[str, Any]) -> dict[str, object]:
    old_name = _require_string(operation, "old_name")
    new_name = _require_string(operation, "new_name")
    if new_name in workbook.sheetnames:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Sheet already exists: {new_name}")
    sheet = _worksheet(workbook, old_name)
    sheet.title = new_name
    return {"type": "rename_sheet", "old_name": old_name, "new_name": new_name}


def _worksheet(workbook, name: str):
    if name not in workbook.sheetnames:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Sheet not found: {name}")
    return workbook[name]


def _require_string(operation: dict[str, Any], key: str) -> str:
    value = operation.get(key)
    if not isinstance(value, str):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"{key} must be a string")
    return value


def _require_int(operation: dict[str, Any], key: str) -> int:
    value = operation.get(key)
    if not isinstance(value, int):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"{key} must be an integer")
    return value
