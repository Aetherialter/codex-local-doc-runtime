from __future__ import annotations

from pathlib import Path
from typing import Any

from docrt.jsonutil import dump_file, dumps
from docrt.timeutil import utc_now_iso


class JsonlLogger:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.degraded = False
        self.last_error: str | None = None
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.degraded = True
            self.last_error = str(exc)

    def write(self, event: dict[str, Any]) -> None:
        if self.degraded:
            return
        try:
            with self.log_path.open("a", encoding="utf-8") as file:
                file.write(dumps(event))
                file.write("\n")
        except OSError as exc:
            self.degraded = True
            self.last_error = str(exc)

    def status(self) -> dict[str, object]:
        return {
            "degraded": self.degraded,
            "last_error": self.last_error,
            "log_path": str(self.log_path),
        }


def write_jsonl_event(path: Path, event: dict[str, Any]) -> dict[str, object]:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(dumps(event))
            file.write("\n")
        return {"ok": True, "path": str(path)}
    except OSError as exc:
        return {"ok": False, "path": str(path), "error": str(exc)}


def error_log_path(logs_dir: Path) -> Path:
    day = utc_now_iso()[:10]
    return logs_dir / "errors" / f"{day}.error.jsonl"


def write_diagnostic(path: Path, payload: dict[str, Any]) -> Path:
    dump_file(path, payload, pretty=True)
    return path


def try_write_diagnostic(path: Path, payload: dict[str, Any]) -> dict[str, object]:
    try:
        write_diagnostic(path, payload)
        return {"ok": True, "path": str(path)}
    except OSError as exc:
        return {"ok": False, "path": str(path), "error": str(exc)}
