from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from docrt.config import Config
from docrt.errors import sanitize_text
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
    paths = _candidate_error_logs(config)
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
            if isinstance(event, dict):
                events.append(event)
    events.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    return events[: max(limit, 0)]


def _candidate_error_logs(config: Config) -> list[Path]:
    errors_dir = config.logs_path / "errors"
    if not errors_dir.exists():
        return []
    return sorted(
        errors_dir.glob("*.error.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True
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
