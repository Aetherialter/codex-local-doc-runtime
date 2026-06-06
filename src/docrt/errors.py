from __future__ import annotations

import hashlib
import re
import sys
import traceback as tb
from pathlib import Path
from typing import Any

from docrt import core_bridge
from docrt.models import ErrorCode
from docrt.paths import ValidationError
from docrt.recovery import recovery_actions
from docrt.timeutil import utc_now_iso

SENSITIVE_KEY_RE = re.compile(r"(token|secret|password|apikey|api_key|authorization)", re.I)
WINDOWS_PATH_RE = re.compile(r"(?<![A-Za-z0-9])([A-Za-z]:\\[^\"'\r\n]+)")
USER_HOME = str(Path.home())


def classify_exception(exc: Exception) -> ErrorCode:
    if isinstance(exc, ValidationError):
        return exc.error_code
    return ErrorCode.UNKNOWN_ERROR


def build_error_event(
    exc: Exception,
    *,
    run_id: str,
    operation: str,
    module: str | None = None,
    function: str | None = None,
    context: dict[str, Any] | None = None,
    level: str = "error",
) -> dict[str, Any]:
    error_code = classify_exception(exc).value
    sanitized_context = sanitize_context(context or {})
    frame = failure_frame(exc)
    resolved_module = module
    resolved_function = function
    if frame:
        resolved_module = frame["module"]
        resolved_function = frame["function"]
    return {
        "schema_version": "1.0",
        "event_id": f"{run_id}-error",
        "run_id": run_id,
        "timestamp": utc_now_iso(),
        "level": level,
        "operation": operation,
        "module": resolved_module,
        "function": resolved_function,
        "error_code": error_code,
        "exception_type": type(exc).__name__,
        "message": sanitize_text(str(exc)),
        "traceback": sanitize_text(tb.format_exc()),
        "context": sanitized_context,
        "environment": {
            "python": sys.version,
            "platform": sys.platform,
            "backend": core_bridge.backend(),
            "rust_available": core_bridge.rust_available(),
            "docrt_core_version": core_bridge.version(),
        },
        "recovery_actions": recovery_actions(error_code),
    }


def failure_frame(exc: Exception) -> dict[str, str] | None:
    traceback = exc.__traceback__
    frames = tb.extract_tb(traceback) if traceback else []
    best: dict[str, str] | None = None
    fallback: dict[str, str] | None = None
    for frame in frames:
        module = _module_from_filename(frame.filename)
        if not module:
            continue
        current = {
            "module": module,
            "function": frame.name,
            "filename": sanitize_text(frame.filename),
            "line": str(frame.lineno),
        }
        if module.startswith("docrt.") and module not in {"docrt.cli", "docrt.runner"}:
            best = current
        elif module.startswith("docrt."):
            fallback = current
    return best or fallback


def sanitize_context(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if SENSITIVE_KEY_RE.search(key_text):
                sanitized[key_text] = "<redacted>"
            elif key_text.endswith("_path") or key_text in {"path", "input", "output"}:
                sanitized[key_text] = summarize_path(item)
            else:
                sanitized[key_text] = sanitize_context(item)
        return sanitized
    if isinstance(value, list):
        return [sanitize_context(item) for item in value[:20]]
    if isinstance(value, tuple):
        return [sanitize_context(item) for item in value[:20]]
    if isinstance(value, str):
        return sanitize_text(value)
    return value


def summarize_path(value: Any) -> dict[str, Any] | Any:
    if not isinstance(value, str | Path):
        return sanitize_context(value)
    text = str(value)
    path = Path(text)
    digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
    return {
        "name": path.name,
        "suffix": path.suffix.lower(),
        "path_hash": f"sha256:{digest}",
    }


def sanitize_text(text: str) -> str:
    sanitized = text.replace(USER_HOME, "<home>")
    sanitized = re.sub(r"(?i)(token|secret|password|api[_-]?key)=\S+", r"\1=<redacted>", sanitized)
    return WINDOWS_PATH_RE.sub(_redact_windows_path, sanitized)


def _redact_windows_path(match: re.Match[str]) -> str:
    raw_path = match.group(1).rstrip()
    trailing = match.group(1)[len(raw_path) :]
    return f"<path:{Path(raw_path).name}>{trailing}"


def _module_from_filename(filename: str) -> str | None:
    path = Path(filename)
    parts = path.with_suffix("").parts
    if "docrt" not in parts:
        return None
    docrt_index = max(index for index, part in enumerate(parts) if part == "docrt")
    module_parts = parts[docrt_index:]
    if not module_parts:
        return None
    return ".".join(module_parts)
