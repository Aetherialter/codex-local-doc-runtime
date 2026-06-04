from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import psutil

OFFICE_PROCESS_NAMES = {"WINWORD.EXE", "EXCEL.EXE"}


@dataclass(frozen=True, slots=True)
class ProcessInfo:
    pid: int
    name: str
    create_time: float | None
    cmdline: list[str]


def snapshot_office_processes() -> dict[int, ProcessInfo]:
    processes: dict[int, ProcessInfo] = {}
    for process in psutil.process_iter(["pid", "name", "create_time", "cmdline"]):
        try:
            name = process.info.get("name") or ""
            if name.upper() in OFFICE_PROCESS_NAMES:
                processes[process.pid] = ProcessInfo(
                    pid=process.pid,
                    name=name,
                    create_time=process.info.get("create_time"),
                    cmdline=process.info.get("cmdline") or [],
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes


def new_office_processes(
    before: dict[int, ProcessInfo], after: dict[int, ProcessInfo]
) -> list[ProcessInfo]:
    return [info for pid, info in after.items() if pid not in before]


def terminate_processes(processes: Iterable[ProcessInfo]) -> list[dict[str, object]]:
    actions = []
    for info in processes:
        try:
            process = psutil.Process(info.pid)
            process.terminate()
            try:
                process.wait(timeout=3)
                status = "terminated"
            except psutil.TimeoutExpired:
                process.kill()
                status = "killed"
            actions.append({"pid": info.pid, "name": info.name, "status": status})
        except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
            actions.append(
                {
                    "pid": info.pid,
                    "name": info.name,
                    "status": "failed",
                    "error": str(exc),
                }
            )
    return actions
