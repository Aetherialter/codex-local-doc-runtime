from __future__ import annotations

from typing import Any

from docrt.config import Config
from docrt.log_analysis import analyze_logs
from docrt.state import write_state

SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}
RISK_RANK = {"low": 1, "medium": 2, "high": 3}


def repair_plan(
    config: Config,
    *,
    days: int = 30,
    limit: int = 200,
    persist: bool = True,
) -> dict[str, object]:
    analysis = analyze_logs(config, days=days, limit=limit)
    items = _plan_items(analysis)
    plan = {
        "days": days,
        "limit": limit,
        "scanned_error_events": analysis["scanned_error_events"],
        "scanned_success_events": analysis["scanned_success_events"],
        "issue_count": analysis["issue_count"],
        "item_count": len(items),
        "items": items,
        "summary": _summary(items),
        "state_path": None,
    }
    if persist:
        plan["state_path"] = str(write_state(config, "repair-plan.latest", plan))
    return plan


def _plan_items(analysis: dict[str, object]) -> list[dict[str, object]]:
    issues = {
        str(issue.get("issue_id")): issue
        for issue in analysis.get("issues", [])
        if isinstance(issue, dict)
    }
    items: list[dict[str, object]] = []
    for recommendation in analysis.get("recommendations", []):
        if not isinstance(recommendation, dict):
            continue
        issue_id = str(recommendation.get("issue_id") or "")
        issue = issues.get(issue_id, {})
        suggested_fix = recommendation.get("suggested_fix")
        if not isinstance(suggested_fix, dict):
            suggested_fix = {}
        severity = str(recommendation.get("severity") or issue.get("severity") or "low")
        risk = str(recommendation.get("risk") or "medium")
        count = int(recommendation.get("count") or issue.get("count") or 0)
        status = str(issue.get("status") or "active")
        category = str(recommendation.get("category") or "repair")
        if category == "unsupported_boundary":
            status = "unsupported_boundary"
        success_after_last_error = bool(issue.get("success_after_last_error"))
        items.append(
            {
                "issue_id": issue_id,
                "priority": _priority(
                    severity,
                    risk,
                    count,
                    success_after_last_error,
                    category,
                ),
                "severity": severity,
                "risk": risk,
                "category": category,
                "status": status,
                "count": count,
                "last_error_at": issue.get("last_seen"),
                "last_success_at": issue.get("last_success_at"),
                "success_after_last_error": success_after_last_error,
                "affected_operations": recommendation.get("affected_operations", []),
                "affected_modules": recommendation.get("affected_modules", []),
                "likely_cause": recommendation.get("likely_cause"),
                "target_files": suggested_fix.get("files", []),
                "suggested_fix": suggested_fix.get("summary"),
                "validation": suggested_fix.get("validation", []),
                "requires_confirmation": bool(recommendation.get("requires_confirmation")),
                "auto_apply_allowed": _auto_apply_allowed(
                    risk,
                    recommendation,
                    success_after_last_error,
                    category,
                ),
                "next_step": _next_step(risk, recommendation, success_after_last_error),
            }
        )
    items.sort(key=_sort_key, reverse=True)
    for index, item in enumerate(items, start=1):
        item["rank"] = index
    return items


def _priority(
    severity: str,
    risk: str,
    count: int,
    success_after_last_error: bool = False,
    category: str = "repair",
) -> str:
    if success_after_last_error or category == "unsupported_boundary":
        return "P4"
    severity_score = SEVERITY_RANK.get(severity, 0)
    risk_score = RISK_RANK.get(risk, 2)
    if severity_score >= 3 and count >= 3:
        return "P0"
    if severity_score >= 3:
        return "P1"
    if severity_score == 2 and risk_score <= 2:
        return "P2"
    return "P3"


def _auto_apply_allowed(
    risk: str,
    recommendation: dict[str, Any],
    success_after_last_error: bool = False,
    category: str = "repair",
) -> bool:
    if success_after_last_error or category == "unsupported_boundary":
        return False
    return risk == "low" and not bool(recommendation.get("requires_confirmation"))


def _next_step(
    risk: str,
    recommendation: dict[str, Any],
    success_after_last_error: bool = False,
) -> str:
    if success_after_last_error:
        return "A later successful run was observed for this operation; keep monitoring logs."
    if recommendation.get("category") == "unsupported_boundary":
        return "This is a documented v1.1 unsupported boundary; adjust the input or workflow."
    if _auto_apply_allowed(risk, recommendation, success_after_last_error):
        return "Implement the low-risk fix in the next development pass, then run validation."
    return "Review the proposed fix before changing core behavior."


def _sort_key(item: dict[str, object]) -> tuple[int, int, int]:
    active = 0 if bool(item.get("success_after_last_error")) else 1
    severity = SEVERITY_RANK.get(str(item["severity"]), 0)
    count = int(item["count"])
    risk = RISK_RANK.get(str(item["risk"]), 2)
    return active, severity, count, -risk


def _summary(items: list[dict[str, object]]) -> dict[str, object]:
    by_priority: dict[str, int] = {}
    requires_confirmation = 0
    auto_apply_allowed = 0
    for item in items:
        priority = str(item["priority"])
        by_priority[priority] = by_priority.get(priority, 0) + 1
        if item["requires_confirmation"]:
            requires_confirmation += 1
        if item["auto_apply_allowed"]:
            auto_apply_allowed += 1
    return {
        "by_priority": by_priority,
        "requires_confirmation": requires_confirmation,
        "auto_apply_allowed": auto_apply_allowed,
    }
