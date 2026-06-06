from __future__ import annotations

import shutil
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from docrt.models import ErrorCode
from docrt.office_com import check_excel_com, check_word_com
from docrt.paths import ValidationError

UV_WINGET_ID = "astral-sh.uv"
_RUNTIME_PREFLIGHT_CONFIRMED: ContextVar[bool] = ContextVar(
    "docrt_runtime_preflight_confirmed", default=False
)


def ensure_uv_available(*, auto_install: bool = True) -> dict[str, object]:
    uv_path = shutil.which("uv")
    if uv_path:
        return {"available": True, "path": uv_path, "installed": False}
    if not auto_install:
        raise ValidationError(
            ErrorCode.UV_UNAVAILABLE,
            "uv is required for the mainline docrt runtime.",
            context=_uv_context(installed=False),
        )
    winget_path = shutil.which("winget")
    if not winget_path:
        raise ValidationError(
            ErrorCode.UV_BOOTSTRAP_FAILED,
            "uv is missing and winget is unavailable, so docrt cannot configure uv automatically.",
            context=_uv_context(installed=False, winget_available=False),
        )
    try:
        completed = subprocess.run(
            [winget_path, "install", "--id", UV_WINGET_ID, "-e", "--accept-package-agreements"],
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except Exception as exc:
        raise ValidationError(
            ErrorCode.UV_BOOTSTRAP_FAILED,
            f"uv automatic bootstrap failed: {exc}",
            context=_uv_context(installed=False, winget_available=True),
        ) from exc
    if completed.returncode != 0:
        raise ValidationError(
            ErrorCode.UV_BOOTSTRAP_FAILED,
            "uv automatic bootstrap failed.",
            context={
                **_uv_context(installed=False, winget_available=True),
                "returncode": completed.returncode,
                "stdout": completed.stdout[-2000:],
                "stderr": completed.stderr[-2000:],
            },
        )
    refreshed = shutil.which("uv")
    return {
        "available": bool(refreshed),
        "path": refreshed,
        "installed": True,
        "restart_shell_recommended": refreshed is None,
    }


def ensure_office_available(
    *,
    require_word: bool = True,
    require_excel: bool = True,
) -> dict[str, object]:
    word_available = check_word_com() if require_word else None
    excel_available = check_excel_com() if require_excel else None
    missing: list[str] = []
    if require_word and not word_available:
        missing.append("Microsoft Word COM")
    if require_excel and not excel_available:
        missing.append("Microsoft Excel COM")
    if missing:
        code = (
            ErrorCode.WORD_COM_UNAVAILABLE
            if missing == ["Microsoft Word COM"]
            else ErrorCode.EXCEL_COM_UNAVAILABLE
            if missing == ["Microsoft Excel COM"]
            else ErrorCode.OFFICE_COM_REQUIRED
        )
        raise ValidationError(
            code,
            "Local Microsoft Office is required for the mainline docrt runtime.",
            context={
                "required": ["Microsoft Word COM", "Microsoft Excel COM"],
                "missing": missing,
                "word_com_available": bool(word_available),
                "excel_com_available": bool(excel_available),
                "current_solution": "no_fallback_yet",
                "doctor_command": "uv run docrt doctor --agent --office-smoke",
            },
        )
    return {
        "word_com_available": bool(word_available) if require_word else None,
        "excel_com_available": bool(excel_available) if require_excel else None,
    }


def ensure_mainline_runtime(*, auto_install_uv: bool = True) -> dict[str, object]:
    uv = ensure_uv_available(auto_install=auto_install_uv)
    office = ensure_office_available(require_word=True, require_excel=True)
    return {
        "runtime": "uv_plus_local_office",
        "uv": uv,
        "office": office,
        "rust": "optional_acceleration_with_python_fallback",
    }


def assert_mainline_runtime_for_path(path: str | Path) -> dict[str, object]:
    suffix = Path(path).suffix.lower()
    if suffix in {".docx", ".pdf", ".xlsx"}:
        if _RUNTIME_PREFLIGHT_CONFIRMED.get():
            return {"runtime": "uv_plus_local_office", "preflight": "already_confirmed"}
        return ensure_mainline_runtime(auto_install_uv=True)
    return {"runtime": "not_document_path", "suffix": suffix}


@contextmanager
def confirmed_mainline_runtime() -> Iterator[None]:
    token = _RUNTIME_PREFLIGHT_CONFIRMED.set(True)
    try:
        yield
    finally:
        _RUNTIME_PREFLIGHT_CONFIRMED.reset(token)


def _uv_context(*, installed: bool, winget_available: bool | None = None) -> dict[str, object]:
    context = {
        "required_entrypoint": "uv run docrt",
        "bootstrap_command": "winget install --id astral-sh.uv -e",
        "installed": installed,
    }
    if winget_available is not None:
        context["winget_available"] = winget_available
    return context
