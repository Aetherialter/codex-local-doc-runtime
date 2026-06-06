from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from docrt.models import ErrorCode

SUPPORTED_EXTENSIONS = {".docx", ".pdf", ".xlsx"}
LEGACY_OFFICE_EXTENSIONS = {".doc", ".xls"}
ZIP_SIGNATURES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
OLE_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


class ValidationError(ValueError):
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}


def normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve().absolute()


def validate_input_path(path: str | Path, extensions: set[str]) -> Path:
    normalized = normalize_path(path)
    if not normalized.exists():
        raise ValidationError(
            ErrorCode.FILE_NOT_FOUND,
            _missing_file_message(path, normalized, extensions),
            context={
                "path_resolution": path_resolution(path),
                "expected_extensions": sorted(extensions),
            },
        )
    if normalized.suffix.lower() not in extensions:
        _raise_unsupported_format(normalized, extensions)
    if len(str(normalized)) > 260:
        raise ValidationError(
            ErrorCode.PATH_VALIDATION_FAILED,
            f"Path exceeds 260 characters and may fail on Windows: {normalized}",
        )
    if not os.access(normalized, os.R_OK):
        raise ValidationError(ErrorCode.PERMISSION_DENIED, f"File is not readable: {normalized}")
    _validate_container_signature(normalized, extensions)
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


def path_resolution(path: str | Path) -> dict[str, object]:
    raw = Path(path).expanduser()
    normalized = normalize_path(path)
    return {
        "input": str(path),
        "is_absolute": raw.is_absolute(),
        "cwd": str(Path.cwd()),
        "resolved": str(normalized),
        "resolved_path": str(normalized),
        "exists": normalized.exists(),
        "suffix": normalized.suffix.lower(),
    }


def _missing_file_message(path: str | Path, normalized: Path, extensions: set[str]) -> str:
    expected = ", ".join(sorted(extensions))
    return (
        f"File not found: {normalized}; original={path!s}; cwd={Path.cwd()}; "
        f"expected_extensions={expected}"
    )


def _raise_unsupported_format(path: Path, extensions: set[str]) -> None:
    suffix = path.suffix.lower()
    if suffix in LEGACY_OFFICE_EXTENSIONS:
        raise ValidationError(
            ErrorCode.UNSUPPORTED_LEGACY_FORMAT,
            f"Legacy Office format is not supported in v1.0: {suffix}",
            context={
                "path_resolution": path_resolution(path),
                "expected_extensions": sorted(extensions),
                "suggested_conversion": ".docx" if suffix == ".doc" else ".xlsx",
            },
        )
    raise ValidationError(
        ErrorCode.UNSUPPORTED_FORMAT,
        f"Unsupported format: {suffix or '<none>'}",
        context={
            "path_resolution": path_resolution(path),
            "expected_extensions": sorted(extensions),
        },
    )


def _validate_container_signature(path: Path, extensions: set[str]) -> None:
    suffix = path.suffix.lower()
    if suffix not in {".docx", ".xlsx"}:
        return
    if suffix not in extensions:
        return
    signature = _read_signature(path)
    if signature.startswith(OLE_SIGNATURE):
        raise ValidationError(
            ErrorCode.ENCRYPTED_FILE_UNSUPPORTED,
            (
                f"{suffix} appears to be an encrypted or legacy OLE Office container; "
                "password-protected Office files are not supported in v1.0"
            ),
            context={
                "path_resolution": path_resolution(path),
                "container_signature": "ole-compound-file",
                "supported_container": "zip-openxml",
            },
        )
    if signature and not any(signature.startswith(item) for item in ZIP_SIGNATURES):
        raise ValidationError(
            ErrorCode.UNSUPPORTED_FORMAT,
            f"{suffix} is not a valid Office Open XML ZIP container",
            context={
                "path_resolution": path_resolution(path),
                "supported_container": "zip-openxml",
            },
        )


def _read_signature(path: Path, size: int = 8) -> bytes:
    try:
        with path.open("rb") as file:
            return file.read(size)
    except OSError as exc:
        raise ValidationError(ErrorCode.PERMISSION_DENIED, f"File is not readable: {path}") from exc
