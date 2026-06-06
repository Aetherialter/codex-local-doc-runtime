from __future__ import annotations

from docrt.config import Config
from docrt.log_analysis import analyze_logs
from docrt.state import runtime_state, write_state
from docrt.storage_ops import storage_report


def maintenance_report(config: Config, *, analyze_days: int = 7) -> dict[str, object]:
    storage = storage_report(config)
    analysis = analyze_logs(config, days=analyze_days, limit=200)
    health = runtime_state(config)
    state_paths = {
        "runtime_state": str(write_state(config, "runtime-state", health)),
        "log_analysis": str(write_state(config, "log-analysis.latest", analysis)),
    }
    return {
        "health": health,
        "storage": storage,
        "log_analysis": analysis,
        "state_paths": state_paths,
        "recommended_actions": _recommended_actions(storage, analysis),
    }


def _recommended_actions(storage: dict[str, object], analysis: dict[str, object]) -> list[str]:
    actions: list[str] = []
    targets = storage.get("targets", [])
    if isinstance(targets, list):
        for target in targets:
            if not isinstance(target, dict):
                continue
            name = target.get("name")
            file_count = int(target.get("file_count", 0))
            size = int(target.get("bytes", 0))
            if name in {"logs", "work", "cache"} and (file_count > 500 or size > 100_000_000):
                actions.append("Run uv run docrt clean --logs --work --cache --older-than 14 --yes")
                break
    if int(analysis.get("issue_count", 0)) > 0:
        actions.append("Run uv run docrt analyze-logs --days 30 before the next maintenance pass")
    return actions
