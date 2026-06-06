from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from docrt.config import Config
from docrt.jsonutil import dump_file
from docrt.timeutil import make_run_id, utc_now_iso

SUPPORTED_BACKGROUND_TASKS = {"maintenance", "analyze-logs", "repair-plan"}


def start_job(config: Config, task: str, *, args: list[str] | None = None) -> dict[str, object]:
    if task not in SUPPORTED_BACKGROUND_TASKS:
        return {
            "started": False,
            "error": f"Unsupported background task: {task}",
            "supported_tasks": sorted(SUPPORTED_BACKGROUND_TASKS),
        }
    job_id = make_run_id()
    jobs_dir = config.state_path / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    status_path = jobs_dir / f"{job_id}.json"
    result_path = jobs_dir / f"{job_id}.result.json"
    command = [
        sys.executable,
        "-m",
        "docrt.job_worker",
        "--job-id",
        job_id,
        "--task",
        task,
        "--status",
        str(status_path),
        "--result",
        str(result_path),
    ]
    if args:
        command.extend(args)
    payload = {
        "job_id": job_id,
        "task": task,
        "status": "queued",
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
        "status_path": str(status_path),
        "result_path": str(result_path),
        "command": command,
    }
    dump_file(status_path, payload)
    process = subprocess.Popen(
        command,
        cwd=Path.cwd(),
        shell=False,
        creationflags=_creationflags(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    payload["status"] = "running"
    payload["pid"] = process.pid
    payload["updated_at"] = utc_now_iso()
    dump_file(status_path, payload)
    return {
        "started": True,
        "job_id": job_id,
        "task": task,
        "pid": process.pid,
        "status_path": str(status_path),
        "result_path": str(result_path),
    }


def job_status(config: Config, job_id: str) -> dict[str, object]:
    status_path = config.state_path / "jobs" / f"{job_id}.json"
    if not status_path.exists():
        return {"found": False, "job_id": job_id, "status_path": str(status_path)}
    data = json.loads(status_path.read_text(encoding="utf-8"))
    return {"found": True, "job": data}


def _creationflags() -> int:
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW
    return 0
