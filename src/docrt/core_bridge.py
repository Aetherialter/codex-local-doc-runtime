from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from docrt.models import ErrorCode
from docrt.paths import ValidationError

try:
    import docrt_core as _rust_core
except Exception:  # Native extension is optional during source checkout.
    _rust_core = None


def rust_available() -> bool:
    return _rust_core is not None


def backend() -> str:
    return "rust" if rust_available() else "python"


def version() -> str:
    if _rust_core is not None:
        return str(_rust_core.version())
    return "python-fallback"


def normalize_slashes(path: str | Path) -> str:
    text = str(path)
    if _rust_core is not None:
        return str(_rust_core.normalize_slashes(text))
    return text.replace("\\", "/")


def sha256_file(path: str | Path) -> str:
    file_path = Path(path)
    if _rust_core is not None:
        return str(_rust_core.sha256_file(str(file_path)))
    hasher = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 64), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def fingerprint(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    if _rust_core is not None:
        return json.loads(str(_rust_core.fingerprint(str(file_path))))
    resolved = file_path.expanduser().resolve(strict=True)
    stat = resolved.stat()
    return {
        "absolute_path": normalize_slashes(resolved),
        "size": stat.st_size,
        "mtime_ms": stat.st_mtime_ns // 1_000_000,
        "sha256": sha256_file(resolved),
        "backend": "python",
    }


def is_path_within_root(root: str | Path, path: str | Path) -> bool:
    if _rust_core is not None:
        return bool(_rust_core.is_path_within_root(str(root), str(path)))
    try:
        root_path = Path(root).expanduser().resolve(strict=True)
        target_path = Path(path).expanduser().resolve(strict=True)
    except OSError:
        return False
    return target_path.is_relative_to(root_path)


def validate_basic_json_object(json_text: str) -> bool:
    if _rust_core is not None:
        try:
            return bool(_rust_core.validate_basic_json_object(json_text))
        except Exception as exc:
            raise ValidationError(
                ErrorCode.VALIDATION_FAILED,
                f"JSON root must be an object: {exc}",
            ) from exc
    try:
        value = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "JSON root must be an object")
    return True
