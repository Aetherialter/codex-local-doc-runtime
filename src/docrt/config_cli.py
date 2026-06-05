from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from docrt.config import Config
from docrt.models import ErrorCode
from docrt.paths import ValidationError

CONFIG_PATH = Path("docrt.config.json")
KEY_ALIASES = {
    "timeout": "default_timeout_seconds",
    "outputs": "outputs_dir",
    "logs": "logs_dir",
    "work": "work_dir",
    "diagnostics": "diagnostics_dir",
    "poppler": "poppler_path",
    "force_kill_office": "allow_force_kill_office",
}


def config_init(*, force: bool = False) -> dict[str, object]:
    if CONFIG_PATH.exists() and not force:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED,
            "docrt.config.json already exists; use --force to overwrite",
        )
    config = Config()
    CONFIG_PATH.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"path": str(CONFIG_PATH.resolve()), "config": asdict(config)}


def config_show(config: Config) -> dict[str, object]:
    return {
        "path": str(CONFIG_PATH.resolve()),
        "exists": CONFIG_PATH.exists(),
        "config": asdict(config),
    }


def config_set(key: str, value: str) -> dict[str, object]:
    key = KEY_ALIASES.get(key, key)
    allowed = set(Config.__dataclass_fields__)
    if key not in allowed:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Unknown config key: {key}")
    data: dict[str, Any] = {}
    if CONFIG_PATH.exists():
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    data[key] = _coerce_value(key, value)
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"path": str(CONFIG_PATH.resolve()), "key": key, "value": data[key]}


def _coerce_value(key: str, value: str) -> object:
    if key == "default_timeout_seconds":
        timeout = int(value)
        return timeout
    if key.endswith("_seconds"):
        return int(value)
    if key == "allow_force_kill_office":
        return value.lower() in {"1", "true", "yes"}
    return value
