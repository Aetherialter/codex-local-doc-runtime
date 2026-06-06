from __future__ import annotations

import json
import msvcrt
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from docrt.config import Config
from docrt.models import ErrorCode
from docrt.office_com import check_excel_com, check_word_com
from docrt.office_process import (
    new_office_processes,
    snapshot_office_processes,
    terminate_processes,
)
from docrt.paths import (
    ValidationError,
    default_pdf_output,
    ensure_output_not_locked,
    ensure_unlocked_for_read,
    validate_input_path,
    validate_output_path,
)

MAX_WORKER_TEXT_CHARS = 4000


def docx_to_pdf(
    input_path: str | Path, output_path: str | Path | None, config: Config, run_id: str
) -> dict[str, object]:
    _ensure_office_available("word")
    source = validate_input_path(input_path, {".docx"})
    ensure_unlocked_for_read(source)
    target = validate_output_path(output_path or default_pdf_output(source, config.outputs_path))
    ensure_output_not_locked(target)
    return _run_worker("word", source, target, config, run_id, config.word_timeout_seconds)


def xlsx_to_pdf(
    input_path: str | Path, output_path: str | Path | None, config: Config, run_id: str
) -> dict[str, object]:
    _ensure_office_available("excel")
    source = validate_input_path(input_path, {".xlsx"})
    ensure_unlocked_for_read(source)
    target = validate_output_path(output_path or default_pdf_output(source, config.outputs_path))
    ensure_output_not_locked(target)
    return _run_worker("excel", source, target, config, run_id, config.excel_timeout_seconds)


def _run_worker(
    kind: str,
    source: Path,
    target: Path,
    config: Config,
    run_id: str,
    timeout: int,
) -> dict[str, object]:
    with _office_conversion_lock(config.work_path, timeout):
        result_json = config.work_path / f"{run_id}.{kind}.result.json"
        before = snapshot_office_processes()
        command = [
            sys.executable,
            "-m",
            "docrt.office_worker",
            kind,
            str(source),
            str(target),
            "--result-json",
            str(result_json),
        ]
        try:
            completed = subprocess.run(
                command,
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired as exc:
            after = snapshot_office_processes()
            created = new_office_processes(before, after)
            cleanup = terminate_processes(created)
            raise ValidationError(
                ErrorCode.OFFICE_TIMEOUT,
                f"{kind} COM conversion timed out after {timeout} seconds; cleanup={cleanup}",
                context={
                    "kind": kind,
                    "input_path": str(source),
                    "output_path": str(target),
                    "timeout_seconds": timeout,
                    "created_office_process_count": len(created),
                    "office_process_cleanup": cleanup,
                    "worker_stdout": _clip_text(exc.stdout),
                    "worker_stderr": _clip_text(exc.stderr),
                },
            ) from exc

        after = snapshot_office_processes()
        created = new_office_processes(before, after)
        cleanup = terminate_processes(created)

        payload = _read_worker_payload(result_json)
        if completed.returncode != 0 or not payload.get("ok"):
            code = (
                ErrorCode.WORD_CONVERSION_FAILED
                if kind == "word"
                else ErrorCode.EXCEL_CONVERSION_FAILED
            )
            raise ValidationError(
                code,
                str(
                    payload.get("error_message") or completed.stderr or f"{kind} conversion failed"
                ),
                context={
                    "kind": kind,
                    "input_path": str(source),
                    "output_path": str(target),
                    "worker_returncode": completed.returncode,
                    "worker_stdout": _clip_text(completed.stdout),
                    "worker_stderr": _clip_text(completed.stderr),
                    "worker_result_json_path": str(result_json),
                    "worker_result": payload,
                    "created_office_process_count": len(created),
                    "office_process_cleanup": cleanup,
                },
            )
        return {
            "input_path": str(source),
            "output_path": str(target),
            "worker_returncode": completed.returncode,
            "worker_stdout": completed.stdout,
            "worker_stderr": completed.stderr,
            "worker_result": payload,
            "office_process_cleanup": cleanup,
        }


@contextmanager
def _office_conversion_lock(work_dir: Path, timeout: int) -> Iterator[None]:
    work_dir.mkdir(parents=True, exist_ok=True)
    lock_path = work_dir / "office-com.lock"
    deadline = time.monotonic() + timeout
    with lock_path.open("a+b") as lock_file:
        while True:
            try:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError as exc:
                if time.monotonic() >= deadline:
                    raise ValidationError(
                        ErrorCode.OFFICE_TIMEOUT,
                        f"Timed out waiting for Office COM conversion lock: {lock_path}",
                    ) from exc
                time.sleep(0.2)
        try:
            yield
        finally:
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)


def _read_worker_payload(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"ok": False, "error_message": f"Worker result was not written: {path}"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "error_message": f"Worker result JSON is invalid: {exc}"}


def _clip_text(value: object) -> str:
    if value is None:
        return ""
    text = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)
    if len(text) <= MAX_WORKER_TEXT_CHARS:
        return text
    return f"{text[:MAX_WORKER_TEXT_CHARS]}...[truncated {len(text) - MAX_WORKER_TEXT_CHARS} chars]"


def _ensure_office_available(kind: str) -> None:
    if kind == "word":
        available = check_word_com()
        code = ErrorCode.WORD_COM_UNAVAILABLE
        app_name = "Microsoft Word"
    else:
        available = check_excel_com()
        code = ErrorCode.EXCEL_COM_UNAVAILABLE
        app_name = "Microsoft Excel"
    if available:
        return
    raise ValidationError(
        code,
        f"{app_name} COM is unavailable; run uv run docrt doctor --agent --office-smoke",
        context={
            "kind": kind,
            "application": app_name,
            "doctor_command": "uv run docrt doctor --agent --office-smoke",
        },
    )
