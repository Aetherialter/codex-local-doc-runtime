from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docrt.core_bridge import validate_basic_json_object
from docrt.models import ErrorCode
from docrt.paths import (
    ValidationError,
    ensure_output_not_locked,
    ensure_unlocked_for_read,
    validate_input_path,
    validate_output_path,
)
from docrt.pdf_safety import ensure_pdf_not_encrypted
from docrt.runtime_env import assert_mainline_runtime_for_path


def annotate_pdf(
    input_path: str | Path, annotations_path: str | Path, output_path: str | Path
) -> dict[str, object]:
    source = validate_input_path(input_path, {".pdf"})
    assert_mainline_runtime_for_path(source)
    annotations_file = validate_input_path(annotations_path, {".json"})
    target = validate_output_path(output_path)
    ensure_unlocked_for_read(source)
    ensure_unlocked_for_read(annotations_file)
    ensure_output_not_locked(target)
    annotations = _load_annotations(annotations_file)

    try:
        import fitz
    except Exception as exc:
        raise RuntimeError("PyMuPDF is unavailable") from exc

    document = fitz.open(str(source))
    applied: list[dict[str, object]] = []
    try:
        ensure_pdf_not_encrypted(document)
        for annotation in annotations:
            applied.append(_apply_annotation(document, annotation))
        document.save(str(target))
    finally:
        document.close()
    return {
        "input_path": str(source),
        "annotations_path": str(annotations_file),
        "output_path": str(target),
        "annotation_count": len(applied),
        "annotations": applied,
    }


def _load_annotations(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    validate_basic_json_object(text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED, f"Annotations JSON is invalid: {exc}"
        ) from exc
    annotations = data.get("annotations")
    if not isinstance(annotations, list) or not annotations:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED,
            "Annotations JSON must contain a non-empty annotations array",
        )
    for index, annotation in enumerate(annotations):
        if not isinstance(annotation, dict) or not isinstance(annotation.get("type"), str):
            raise ValidationError(
                ErrorCode.VALIDATION_FAILED,
                f"Annotation at index {index} must be an object with a string type",
            )
    return annotations


def _apply_annotation(document, annotation: dict[str, Any]) -> dict[str, object]:
    page_number = _require_int(annotation, "page_number")
    if page_number < 1 or page_number > document.page_count:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Page out of range: {page_number}")
    page = document[page_number - 1]
    annotation_type = annotation["type"]
    if annotation_type == "highlight":
        rect = _rect(annotation)
        annot = page.add_highlight_annot(rect)
    elif annotation_type == "rectangle":
        rect = _rect(annotation)
        annot = page.add_rect_annot(rect)
    elif annotation_type == "text_note":
        point = _point(annotation)
        annot = page.add_text_annot(point, _require_string(annotation, "text"))
    elif annotation_type == "stamp":
        point = _point(annotation)
        annot = page.add_text_annot(point, _require_string(annotation, "text"))
        annot.set_name("Stamp")
    else:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED,
            f"Unsupported PDF annotation type: {annotation_type}",
        )
    annot.update()
    return {"type": annotation_type, "page_number": page_number}


def _rect(annotation: dict[str, Any]):
    bbox = annotation.get("bbox")
    if not (
        isinstance(bbox, list)
        and len(bbox) == 4
        and all(isinstance(value, int | float) for value in bbox)
    ):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "bbox must be [x0, y0, x1, y1]")
    try:
        import fitz
    except Exception as exc:
        raise RuntimeError("PyMuPDF is unavailable") from exc
    return fitz.Rect(*bbox)


def _point(annotation: dict[str, Any]):
    point = annotation.get("point")
    if not (
        isinstance(point, list)
        and len(point) == 2
        and all(isinstance(value, int | float) for value in point)
    ):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "point must be [x, y]")
    try:
        import fitz
    except Exception as exc:
        raise RuntimeError("PyMuPDF is unavailable") from exc
    return fitz.Point(*point)


def _require_string(annotation: dict[str, Any], key: str) -> str:
    value = annotation.get(key)
    if not isinstance(value, str):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"{key} must be a string")
    return value


def _require_int(annotation: dict[str, Any], key: str) -> int:
    value = annotation.get(key)
    if not isinstance(value, int):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"{key} must be an integer")
    return value
