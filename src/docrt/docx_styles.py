from __future__ import annotations


def paragraph_style_name(paragraph) -> str:
    style = getattr(paragraph, "style", None)
    name = getattr(style, "name", None)
    return name if isinstance(name, str) else ""


def is_heading_style(style_name: str) -> bool:
    normalized = style_name.casefold()
    return normalized.startswith("heading") or normalized.startswith("标题")
