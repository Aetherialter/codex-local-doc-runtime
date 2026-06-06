from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path

from docrt.config import Config
from docrt.errors import build_error_event, classify_exception
from docrt.jsonutil import dump_file
from docrt.log_analysis import analyze_logs
from docrt.logging import error_log_path, try_write_diagnostic, write_jsonl_event
from docrt.maintenance import maintenance_report
from docrt.repair_plan import repair_plan
from docrt.storage_ops import clean
from docrt.timeutil import utc_now_iso


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument(
        "--task",
        required=True,
        choices=["maintenance", "analyze-logs", "repair-plan", "clean-retention"],
    )
    parser.add_argument("--status", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()

    status_path = Path(args.status)
    result_path = Path(args.result)
    config = Config.load()
    _update_status(status_path, status="running")
    try:
        if args.task == "maintenance":
            data = maintenance_report(config, analyze_days=args.days)
        elif args.task == "analyze-logs":
            data = analyze_logs(config, days=args.days)
        elif args.task == "clean-retention":
            data = clean(config, retention=True, yes=args.yes, include_files=False)
        else:
            data = repair_plan(config, days=args.days)
        result = {
            "ok": True,
            "job_id": args.job_id,
            "task": args.task,
            "finished_at": utc_now_iso(),
            "data": data,
        }
        dump_file(result_path, result)
        _update_status(status_path, status="succeeded", result_path=str(result_path))
        return 0
    except Exception as exc:
        error_event = build_error_event(
            exc,
            run_id=args.job_id,
            operation=f"job:{args.task}",
            module="docrt.job_worker",
            function="main",
            context={
                "job_id": args.job_id,
                "task": args.task,
                "status_path": str(status_path),
                "result_path": str(result_path),
                "days": args.days,
                "yes": args.yes,
            },
        )
        error_log_status = write_jsonl_event(error_log_path(config.logs_path), error_event)
        diagnostic_path = config.diagnostics_path / f"{args.job_id}.job.diagnostic.json"
        result = {
            "ok": False,
            "job_id": args.job_id,
            "task": args.task,
            "finished_at": utc_now_iso(),
            "error_code": classify_exception(exc).value,
            "error_message": str(exc),
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
            "error_event_log": error_log_status,
            "diagnostic_report_path": str(diagnostic_path),
        }
        diagnostic_status = try_write_diagnostic(
            diagnostic_path,
            {
                "result": result,
                "error_event": error_event,
                "generated_at": utc_now_iso(),
            },
        )
        if not diagnostic_status["ok"]:
            result["diagnostic_report_path"] = None
            result["diagnostic_write"] = diagnostic_status
        dump_file(result_path, result)
        _update_status(
            status_path,
            status="failed",
            result_path=str(result_path),
            error_code=result["error_code"],
            diagnostic_report_path=result["diagnostic_report_path"],
        )
        return 1


def _update_status(path: Path, **updates: object) -> None:
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    data.update(updates)
    data["updated_at"] = utc_now_iso()
    dump_file(path, data)


if __name__ == "__main__":
    raise SystemExit(main())
