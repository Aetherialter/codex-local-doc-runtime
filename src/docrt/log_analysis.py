from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from docrt.config import Config
from docrt.errors import sanitize_context, sanitize_text
from docrt.repair_advisor import recommendations_for_issue


def analyze_logs(
    config: Config,
    *,
    days: int = 7,
    limit: int = 200,
    include_events: bool = False,
) -> dict[str, object]:
    events = _load_error_events(config, days=days, limit=limit)
    issues = _summarize_events(events)
    recommendations = []
    for issue in issues:
        recommendations.extend(recommendations_for_issue(issue))
    return {
        "days": days,
        "limit": limit,
        "scanned_error_events": len(events),
        "issue_count": len(issues),
        "issues": issues,
        "recommendations": recommendations,
        "events": events if include_events else [],
    }


def recent_errors(config: Config, *, limit: int = 20) -> dict[str, object]:
    events = _load_error_events(config, days=30, limit=limit)
    return {"limit": limit, "count": len(events), "events": events}


def _load_error_events(config: Config, *, days: int, limit: int) -> list[dict[str, Any]]:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    paths = _candidate_logs(config)
    events: list[dict[str, Any]] = []
    for path in paths:
        if _mtime(path) < cutoff:
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            normalized = _normalize_error_event(event, source_path=path)
            if normalized is not None:
                events.append(normalized)
    events.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    return _dedupe_events(events)[: max(limit, 0)]


def _candidate_logs(config: Config) -> list[Path]:
    paths = [*_candidate_error_logs(config), *_candidate_run_logs(config)]
    seen: set[Path] = set()
    result: list[Path] = []
    for path in sorted(paths, key=lambda item: item.stat().st_mtime, reverse=True):
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        result.append(path)
    return result


def _candidate_error_logs(config: Config) -> list[Path]:
    errors_dir = config.logs_path / "errors"
    if not errors_dir.exists():
        return []
    return sorted(
        errors_dir.glob("*.error.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True
    )


def _candidate_run_logs(config: Config) -> list[Path]:
    if not config.logs_path.exists():
        return []
    return sorted(
        config.logs_path.glob("*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True
    )


def _normalize_error_event(event: dict[str, Any], *, source_path: Path) -> dict[str, Any] | None:
    if event.get("level") in {"error", "critical"} and event.get("error_code"):
        return {**event, "source_log": str(source_path)}
    if event.get("error_code") and event.get("operation"):
        return {
            **event,
            "level": event.get("level") or "error",
            "source_log": str(source_path),
        }
    result = event.get("result")
    if not isinstance(result, dict) or result.get("ok") is not False:
        return None
    error_code = str(result.get("error_code") or "UNKNOWN_ERROR")
    run_id = str(result.get("run_id") or source_path.stem)
    return {
        "schema_version": "1.0",
        "event_id": f"{run_id}-error",
        "run_id": run_id,
        "timestamp": result.get("ended_at") or event.get("timestamp") or "",
        "level": "error",
        "operation": result.get("operation") or event.get("operation") or "unknown",
        "module": result.get("backend") or "unknown",
        "function": None,
        "error_code": error_code,
        "exception_type": result.get("exception_type") or "unknown",
        "message": sanitize_text(str(result.get("error_message") or "")),
        "traceback": sanitize_text(str(result.get("traceback") or "")),
        "context": sanitize_context(
            {
                "input_path": result.get("input_path"),
                "output_path": result.get("output_path"),
                "backend": result.get("backend"),
            }
        ),
        "environment": {},
        "recovery_actions": result.get("recovery_actions") or [],
        "source_log": str(source_path),
    }


def _dedupe_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for event in events:
        key = _event_key(event)
        if key in seen:
            continue
        seen.add(key)
        result.append(event)
    return result


def _event_key(event: dict[str, Any]) -> tuple[str, ...]:
    event_id = event.get("event_id")
    if event_id:
        return ("event_id", str(event_id))
    return (
        "fallback",
        str(event.get("run_id") or ""),
        str(event.get("operation") or ""),
        str(event.get("error_code") or ""),
        str(event.get("exception_type") or ""),
        str(event.get("timestamp") or ""),
    )


def _summarize_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        error_code = str(event.get("error_code") or "UNKNOWN_ERROR")
        operation = str(event.get("operation") or "unknown")
        buckets[(error_code, operation)].append(event)

    issues = []
    for (error_code, operation), bucket in buckets.items():
        modules = Counter(str(event.get("module") or "unknown") for event in bucket)
        exception_types = Counter(str(event.get("exception_type") or "unknown") for event in bucket)
        issue_id = f"{error_code}:{operation}"
        issues.append(
            {
                "issue_id": issue_id,
                "error_code": error_code,
                "operation": operation,
                "count": len(bucket),
                "severity": _severity(error_code, len(bucket)),
                "modules": [name for name, _count in modules.most_common()],
                "exception_types": [name for name, _count in exception_types.most_common()],
                "first_seen": min(str(event.get("timestamp") or "") for event in bucket),
                "last_seen": max(str(event.get("timestamp") or "") for event in bucket),
                "sample_message": sanitize_text(str(bucket[0].get("message") or "")),
            }
        )
    issues.sort(
        key=lambda item: (_severity_rank(str(item["severity"])), int(item["count"])), reverse=True
    )
    return issues


def _severity(error_code: str, count: int) -> str:
    if error_code in {
        "OFFICE_TIMEOUT",
        "WORD_CONVERSION_FAILED",
        "EXCEL_CONVERSION_FAILED",
        "UNKNOWN_ERROR",
    }:
        return "high"
    if count >= 5:
        return "high"
    if error_code in {"VALIDATION_FAILED", "FILE_LOCKED", "FILE_NOT_FOUND"}:
        return "medium"
    return "low"


def _severity_rank(severity: str) -> int:
    return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(severity, 0)


def _mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, UTC)
