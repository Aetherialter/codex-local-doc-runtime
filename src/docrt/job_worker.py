from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path

from docrt.config import Config
from docrt.jsonutil import dump_file
from docrt.log_analysis import analyze_logs
from docrt.maintenance import maintenance_report
from docrt.repair_plan import repair_plan
from docrt.timeutil import utc_now_iso


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument(
        "--task",
        required=True,
        choices=["maintenance", "analyze-logs", "repair-plan"],
    )
    parser.add_argument("--status", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--days", type=int, default=7)
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
        result = {
            "ok": False,
            "job_id": args.job_id,
            "task": args.task,
            "finished_at": utc_now_iso(),
            "error_message": str(exc),
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        }
        dump_file(result_path, result)
        _update_status(status_path, status="failed", result_path=str(result_path))
        return 1


def _update_status(path: Path, **updates: object) -> None:
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    data.update(updates)
    data["updated_at"] = utc_now_iso()
    dump_file(path, data)


if __name__ == "__main__":
    raise SystemExit(main())
