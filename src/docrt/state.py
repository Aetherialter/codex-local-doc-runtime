from __future__ import annotations

from pathlib import Path
from typing import Any

from docrt.config import Config
from docrt.jsonutil import dump_file
from docrt.timeutil import utc_now_iso


def write_state(config: Config, name: str, data: dict[str, Any]) -> Path:
    path = config.state_path / f"{name}.json"
    payload = {
        "schema_version": "1.0",
        "updated_at": utc_now_iso(),
        "name": name,
        "data": data,
    }
    dump_file(path, payload)
    return path


def read_state(config: Config, name: str) -> dict[str, Any] | None:
    path = config.state_path / f"{name}.json"
    if not path.exists():
        return None
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def runtime_state(config: Config) -> dict[str, object]:
    return {
        "paths": {
            "logs": str(config.logs_path),
            "outputs": str(config.outputs_path),
            "work": str(config.work_path),
            "diagnostics": str(config.diagnostics_path),
            "state": str(config.state_path),
        },
        "retention": {
            "logs_days": config.log_retention_days,
            "diagnostics_days": config.diagnostic_retention_days,
            "cache_days": config.cache_retention_days,
        },
    }
