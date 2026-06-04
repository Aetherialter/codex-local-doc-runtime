from __future__ import annotations

import os
from pathlib import Path

from docrt.models import ErrorCode

SUPPORTED_EXTENSIONS = {".docx", ".pdf", ".xlsx"}


class ValidationError(ValueError):
    def __init__(self, error_code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


def normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve().absolute()


def validate_input_path(path: str | Path, extensions: set[str]) -> Path:
    normalized = normalize_path(path)
    if not normalized.exists():
        raise ValidationError(ErrorCode.FILE_NOT_FOUND, f"File not found: {normalized}")
    if normalized.suffix.lower() not in extensions:
        raise ValidationError(
            ErrorCode.UNSUPPORTED_FORMAT,
            f"Unsupported format: {normalized.suffix or '<none>'}",
        )
    if len(str(normalized)) > 260:
        raise ValidationError(
            ErrorCode.PATH_VALIDATION_FAILED,
            f"Path exceeds 260 characters and may fail on Windows: {normalized}",
        )
    if not os.access(normalized, os.R_OK):
        raise ValidationError(ErrorCode.PERMISSION_DENIED, f"File is not readable: {normalized}")
    return normalized


def validate_output_path(path: str | Path) -> Path:
    normalized = normalize_path(path)
    if len(str(normalized)) > 260:
        raise ValidationError(
            ErrorCode.PATH_VALIDATION_FAILED,
            f"Path exceeds 260 characters and may fail on Windows: {normalized}",
        )
    normalized.parent.mkdir(parents=True, exist_ok=True)
    if not os.access(normalized.parent, os.W_OK):
        raise ValidationError(
            ErrorCode.PERMISSION_DENIED,
            f"Output directory is not writable: {normalized.parent}",
        )
    return normalized


def ensure_unlocked_for_read(path: Path) -> None:
    try:
        with path.open("rb"):
            pass
    except PermissionError as exc:
        raise ValidationError(ErrorCode.FILE_LOCKED, f"File is locked: {path}") from exc


def ensure_output_not_locked(path: Path) -> None:
    if not path.exists():
        return
    try:
        with path.open("ab"):
            pass
    except PermissionError as exc:
        raise ValidationError(ErrorCode.FILE_LOCKED, f"Output file is locked: {path}") from exc


def default_pdf_output(input_path: Path, outputs_dir: Path) -> Path:
    return outputs_dir / f"{input_path.stem}.pdf"


def default_inspect_output(input_path: Path, outputs_dir: Path) -> Path:
    return outputs_dir / f"{input_path.name}.inspect.json"


def default_render_output_dir(input_path: Path, outputs_dir: Path) -> Path:
    return outputs_dir / input_path.stem
