from __future__ import annotations

from pathlib import Path

from docrt.read_ops import read_docx, read_xlsx


def verify_docx(before_path: str | Path, after_path: str | Path) -> dict[str, object]:
    before = read_docx(before_path)
    after = read_docx(after_path)
    return _verify_read_results("docx", before, after)


def verify_xlsx(before_path: str | Path, after_path: str | Path) -> dict[str, object]:
    before = read_xlsx(before_path)
    after = read_xlsx(after_path)
    return _verify_read_results("xlsx", before, after)


def _verify_read_results(
    document_type: str, before: dict[str, object], after: dict[str, object]
) -> dict[str, object]:
    before_blocks = before.get("content_blocks", [])
    after_blocks = after.get("content_blocks", [])
    before_tables = before.get("tables", [])
    after_tables = after.get("tables", [])
    changed = before_blocks != after_blocks or before_tables != after_tables
    return {
        "document_type": document_type,
        "before_path": before.get("path"),
        "after_path": after.get("path"),
        "changed": changed,
        "summary": {
            "before_content_blocks": len(before_blocks) if isinstance(before_blocks, list) else 0,
            "after_content_blocks": len(after_blocks) if isinstance(after_blocks, list) else 0,
            "before_tables": len(before_tables) if isinstance(before_tables, list) else 0,
            "after_tables": len(after_tables) if isinstance(after_tables, list) else 0,
        },
        "warnings": [*before.get("warnings", []), *after.get("warnings", [])],
    }
