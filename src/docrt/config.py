from __future__ import annotations

import json
import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from docrt.models import ErrorCode
from docrt.paths import ValidationError


@dataclass(frozen=True, slots=True)
class Config:
    default_timeout_seconds: int = 30
    word_timeout_seconds: int = 30
    excel_timeout_seconds: int = 30
    poppler_timeout_seconds: int = 30
    allow_force_kill_office: bool = False
    poppler_path: str | None = None
    outputs_dir: str = "outputs"
    logs_dir: str = "logs"
    work_dir: str = "work"
    diagnostics_dir: str = "outputs/diagnostics"
    state_dir: str = "state"
    log_retention_days: int = 14
    diagnostic_retention_days: int = 30
    cache_retention_days: int = 14

    @classmethod
    def load(
        cls,
        *,
        project_root: Path | None = None,
        poppler_path: str | None = None,
        timeout: int | None = None,
        force_kill_office: bool = False,
    ) -> Config:
        root = project_root or Path.cwd()
        config = cls()
        file_values = _read_config_file(root / "docrt.config.json")
        config = _merge(config, file_values)
        config = _merge(config, _env_values())

        overrides: dict[str, Any] = {}
        if poppler_path:
            overrides["poppler_path"] = poppler_path
        if timeout is not None:
            overrides["default_timeout_seconds"] = timeout
            overrides["word_timeout_seconds"] = timeout
            overrides["excel_timeout_seconds"] = timeout
            overrides["poppler_timeout_seconds"] = timeout
        if force_kill_office:
            overrides["allow_force_kill_office"] = True
        return _merge(config, overrides)

    def path_for(self, value: str) -> Path:
        return Path(value).expanduser().resolve().absolute()

    @property
    def outputs_path(self) -> Path:
        return self.path_for(self.outputs_dir)

    @property
    def logs_path(self) -> Path:
        return self.path_for(self.logs_dir)

    @property
    def work_path(self) -> Path:
        return self.path_for(self.work_dir)

    @property
    def diagnostics_path(self) -> Path:
        return self.path_for(self.diagnostics_dir)

    @property
    def state_path(self) -> Path:
        return self.path_for(self.state_dir)


def _read_config_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _env_values() -> dict[str, Any]:
    values: dict[str, Any] = {}
    env_map = {
        "DOCRT_OUTPUTS_DIR": "outputs_dir",
        "DOCRT_LOGS_DIR": "logs_dir",
        "DOCRT_WORK_DIR": "work_dir",
        "DOCRT_DIAGNOSTICS_DIR": "diagnostics_dir",
        "DOCRT_STATE_DIR": "state_dir",
        "POPPLER_PATH": "poppler_path",
    }
    for env_name, key in env_map.items():
        if os.getenv(env_name):
            values[key] = os.environ[env_name]
    if os.getenv("DOCRT_TIMEOUT_SECONDS"):
        timeout = _coerce_positive_int("DOCRT_TIMEOUT_SECONDS", os.environ["DOCRT_TIMEOUT_SECONDS"])
        values["default_timeout_seconds"] = timeout
        values["word_timeout_seconds"] = timeout
        values["excel_timeout_seconds"] = timeout
        values["poppler_timeout_seconds"] = timeout
    if os.getenv("DOCRT_ALLOW_FORCE_KILL_OFFICE"):
        values["allow_force_kill_office"] = os.environ["DOCRT_ALLOW_FORCE_KILL_OFFICE"].lower() in {
            "1",
            "true",
            "yes",
        }
    return values


def _merge(config: Config, values: dict[str, Any]) -> Config:
    allowed = set(Config.__dataclass_fields__)
    clean = {
        _key: _coerce_config_value(_key, value) for _key, value in values.items() if _key in allowed
    }
    return replace(config, **clean)


def _coerce_config_value(key: str, value: Any) -> Any:
    if key.endswith("_seconds") or key.endswith("_days"):
        return _coerce_positive_int(key, value)
    if key == "allow_force_kill_office" and isinstance(value, str):
        return value.lower() in {"1", "true", "yes"}
    return value


def _coerce_positive_int(key: str, value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED,
            f"Config value {key} must be an integer, got {value!r}",
        ) from exc
    if number < 0:
        raise ValidationError(
            ErrorCode.VALIDATION_FAILED,
            f"Config value {key} must be non-negative, got {number}",
        )
    return number
