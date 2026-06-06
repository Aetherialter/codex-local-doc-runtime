from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from docrt.config import Config
from docrt.core_bridge import is_path_within_root
from docrt.models import ErrorCode
from docrt.paths import ValidationError


@dataclass(frozen=True, slots=True)
class CleanTarget:
    name: str
    path: Path


def storage_report(config: Config) -> dict[str, object]:
    targets = _all_targets(config)
    return {"targets": [_target_report(target) for target in targets]}


def clean(
    config: Config,
    *,
    older_than_days: int | None = None,
    yes: bool = False,
    include_files: bool = True,
    retention: bool = False,
    logs: bool = False,
    outputs: bool = False,
    work: bool = False,
    diagnostics: bool = False,
    cache: bool = False,
    dist: bool = False,
    all_targets: bool = False,
) -> dict[str, object]:
    selected = _selected_targets(
        config,
        logs=logs,
        outputs=outputs,
        work=work,
        diagnostics=diagnostics,
        cache=cache,
        dist=dist,
        all_targets=all_targets,
    )
    retention_days = _retention_days_by_target(config) if retention else {}
    if retention and not selected:
        selected = _retention_targets(config)
    cutoff = _cutoff_for_days(older_than_days)
    files = []
    seen_files: set[Path] = set()
    policy: list[dict[str, object]] = []
    for target in selected:
        _ensure_safe_target(target.path)
        target_days = retention_days.get(target.name)
        if retention and target_days is None and older_than_days is None:
            policy.append(
                {
                    "target": target.name,
                    "older_than_days": None,
                    "skipped": True,
                    "reason": "no_retention_policy",
                }
            )
            continue
        target_cutoff = _cutoff_for_days(target_days) if target_days is not None else cutoff
        effective_days = target_days if target_days is not None else older_than_days
        policy.append(
            {
                "target": target.name,
                "older_than_days": effective_days,
                "skipped": False,
            }
        )
        for path in _iter_files(target.path):
            resolved_path = path.resolve()
            if resolved_path in seen_files:
                continue
            seen_files.add(resolved_path)
            if target_cutoff and _mtime(path) >= target_cutoff:
                continue
            files.append({"target": target.name, "path": str(path), "bytes": path.stat().st_size})
    deleted = []
    if yes:
        for item in files:
            path = Path(str(item["path"]))
            path.unlink(missing_ok=True)
            deleted.append(item)
        _remove_empty_dirs(selected)
    return {
        "dry_run": not yes,
        "retention": retention,
        "older_than_days": older_than_days,
        "policy": policy,
        "selected_targets": [target.name for target in selected],
        "planned_count": len(files),
        "planned_bytes": sum(int(item["bytes"]) for item in files),
        "deleted_count": len(deleted),
        "deleted_bytes": sum(int(item["bytes"]) for item in deleted),
        "files": files if include_files else [],
        "files_omitted": 0 if include_files else len(files),
    }


def _all_targets(config: Config) -> list[CleanTarget]:
    return [
        CleanTarget("logs", config.logs_path),
        CleanTarget("outputs", config.outputs_path),
        CleanTarget("work", config.work_path),
        CleanTarget("diagnostics", config.diagnostics_path),
        CleanTarget("cache", config.work_path / "cache"),
        CleanTarget("state", config.state_path),
        CleanTarget("dist", Path.cwd() / "dist"),
    ]


def _selected_targets(
    config: Config,
    *,
    logs: bool,
    outputs: bool,
    work: bool,
    diagnostics: bool,
    cache: bool,
    dist: bool,
    all_targets: bool,
) -> list[CleanTarget]:
    targets = _all_targets(config)
    if all_targets:
        return _dedupe_targets(targets)
    selected_names = {
        name
        for name, enabled in {
            "logs": logs,
            "outputs": outputs,
            "work": work,
            "diagnostics": diagnostics,
            "cache": cache,
            "dist": dist,
        }.items()
        if enabled
    }
    return _dedupe_targets([target for target in targets if target.name in selected_names])


def _retention_targets(config: Config) -> list[CleanTarget]:
    targets_by_name = {target.name: target for target in _all_targets(config)}
    return _dedupe_targets(
        [
            targets_by_name["logs"],
            targets_by_name["diagnostics"],
            targets_by_name["cache"],
        ]
    )


def _retention_days_by_target(config: Config) -> dict[str, int]:
    return {
        "logs": config.log_retention_days,
        "work": config.cache_retention_days,
        "diagnostics": config.diagnostic_retention_days,
        "cache": config.cache_retention_days,
    }


def _cutoff_for_days(days: int | None) -> datetime | None:
    return datetime.now(UTC) - timedelta(days=days) if days is not None else None


def _dedupe_targets(targets: list[CleanTarget]) -> list[CleanTarget]:
    result: list[CleanTarget] = []
    seen: set[Path] = set()
    for target in targets:
        resolved = target.path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        result.append(target)
    return result


def _ensure_safe_target(path: Path) -> None:
    root = Path.cwd().resolve()
    resolved = path.resolve()
    check_path = resolved if resolved.exists() else _nearest_existing_parent(resolved)
    if not is_path_within_root(root, check_path):
        raise ValidationError(
            ErrorCode.PATH_VALIDATION_FAILED,
            f"Refusing to clean outside project root: {resolved}",
        )


def _nearest_existing_parent(path: Path) -> Path:
    current = path
    while not current.exists() and current.parent != current:
        current = current.parent
    return current


def _iter_files(path: Path):
    if not path.exists():
        return
    for item in path.rglob("*"):
        if item.is_file() and not item.is_symlink():
            yield item


def _remove_empty_dirs(targets: list[CleanTarget]) -> None:
    for target in targets:
        if not target.path.exists():
            continue
        for path in sorted(target.path.rglob("*"), key=lambda item: len(item.parts), reverse=True):
            if path.is_dir():
                with suppress(OSError):
                    path.rmdir()


def _mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, UTC)


def _target_report(target: CleanTarget) -> dict[str, object]:
    files = list(_iter_files(target.path) or [])
    oldest = min((_mtime(path) for path in files), default=None)
    return {
        "name": target.name,
        "path": str(target.path),
        "exists": target.path.exists(),
        "file_count": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "oldest_file_time": oldest.isoformat() if oldest else None,
    }
