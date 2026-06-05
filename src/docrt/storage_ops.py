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
    return {
        "targets": [
            {
                "name": target.name,
                "path": str(target.path),
                "exists": target.path.exists(),
                "file_count": _file_count(target.path),
                "bytes": _dir_size(target.path),
            }
            for target in targets
        ]
    }


def clean(
    config: Config,
    *,
    older_than_days: int | None = None,
    yes: bool = False,
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
    cutoff = (
        datetime.now(UTC) - timedelta(days=older_than_days) if older_than_days is not None else None
    )
    files = []
    seen_files: set[Path] = set()
    for target in selected:
        _ensure_safe_target(target.path)
        for path in _iter_files(target.path):
            resolved_path = path.resolve()
            if resolved_path in seen_files:
                continue
            seen_files.add(resolved_path)
            if cutoff and _mtime(path) >= cutoff:
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
        "older_than_days": older_than_days,
        "selected_targets": [target.name for target in selected],
        "planned_count": len(files),
        "planned_bytes": sum(int(item["bytes"]) for item in files),
        "deleted_count": len(deleted),
        "deleted_bytes": sum(int(item["bytes"]) for item in deleted),
        "files": files,
    }


def _all_targets(config: Config) -> list[CleanTarget]:
    return [
        CleanTarget("logs", config.logs_path),
        CleanTarget("outputs", config.outputs_path),
        CleanTarget("work", config.work_path),
        CleanTarget("diagnostics", config.diagnostics_path),
        CleanTarget("cache", config.work_path / "cache"),
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


def _dir_size(path: Path) -> int:
    return sum(item.stat().st_size for item in _iter_files(path) or [])


def _file_count(path: Path) -> int:
    return sum(1 for _ in _iter_files(path) or [])


def _mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, UTC)
