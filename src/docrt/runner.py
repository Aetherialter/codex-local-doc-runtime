from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from docrt.config import Config
from docrt.errors import build_error_event, classify_exception
from docrt.logging import JsonlLogger, error_log_path, try_write_diagnostic, write_jsonl_event
from docrt.models import ErrorCode, Result
from docrt.timeutil import Timer, make_run_id, utc_now_iso


def run_operation(
    operation: str,
    handler: Callable[[str, Config, JsonlLogger], dict[str, Any]],
    *,
    config: Config,
    run_id: str | None = None,
    input_path: Path | None = None,
    output_path: Path | None = None,
    backend: str | None = None,
) -> Result:
    actual_run_id = run_id or make_run_id()
    log_path = config.logs_path / f"{actual_run_id}.jsonl"
    diagnostic_path = config.diagnostics_path / f"{actual_run_id}.diagnostic.json"
    logger = JsonlLogger(log_path)
    timer = Timer()
    logger.write(
        {
            "run_id": actual_run_id,
            "operation": operation,
            "event": "started",
            "input_path": str(input_path) if input_path else None,
            "output_path": str(output_path) if output_path else None,
            "backend": backend,
            "timestamp": timer.started_at,
        }
    )
    try:
        data = handler(actual_run_id, config, logger)
        ended_at, duration_ms = timer.finish()
        result = Result(
            ok=True,
            operation=operation,
            input_path=str(input_path) if input_path else None,
            output_path=str(output_path) if output_path else None,
            backend=backend,
            run_id=actual_run_id,
            started_at=timer.started_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
            log_path=str(log_path),
            data=data,
        )
    except Exception as exc:  # CLI/library boundary intentionally converts failures.
        ended_at, duration_ms = timer.finish()
        error_code = _classify(exc)
        error_event = build_error_event(
            exc,
            run_id=actual_run_id,
            operation=operation,
            module=getattr(handler, "__module__", None),
            function=getattr(handler, "__name__", None),
            context={
                "input_path": str(input_path) if input_path else None,
                "output_path": str(output_path) if output_path else None,
                "backend": backend,
            },
        )
        error_log_status = write_jsonl_event(error_log_path(config.logs_path), error_event)
        result = Result(
            ok=False,
            operation=operation,
            input_path=str(input_path) if input_path else None,
            output_path=str(output_path) if output_path else None,
            backend=backend,
            run_id=actual_run_id,
            started_at=timer.started_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
            error_code=error_code.value,
            error_message=str(exc),
            exception_type=type(exc).__name__,
            traceback=error_event["traceback"],
            recovery_actions=list(error_event["recovery_actions"]),
            diagnostic_report_path=str(diagnostic_path),
            log_path=str(log_path),
            data={
                "error_event_log": error_log_status,
            },
        )
        diagnostic_status = try_write_diagnostic(
            diagnostic_path,
            {
                "result": result.to_dict(),
                "error_event": error_event,
                "generated_at": utc_now_iso(),
            },
        )
        if not diagnostic_status["ok"]:
            result.diagnostic_report_path = None
            result.data["diagnostic_write"] = diagnostic_status
    logger.write(
        {
            "run_id": actual_run_id,
            "operation": operation,
            "event": "finished",
            "result": result.to_dict(),
            "logging": logger.status(),
        }
    )
    if logger.degraded:
        result.data.setdefault("warnings", []).append("run log writing degraded")
    return result


def _classify(exc: Exception) -> ErrorCode:
    return classify_exception(exc)
