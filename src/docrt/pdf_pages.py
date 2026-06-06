from __future__ import annotations

from docrt.models import ErrorCode
from docrt.paths import ValidationError


def selected_page_indexes(page_count: int, pages: str | None = None) -> list[int]:
    if page_count < 0:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "page_count must not be negative")
    if not pages:
        return list(range(page_count))
    selected: list[int] = []
    seen: set[int] = set()
    for part in pages.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = _parse_page_number(start_text)
            end = _parse_page_number(end_text)
            if start > end:
                raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Invalid page range: {token}")
            numbers = range(start, end + 1)
        else:
            numbers = range(_parse_page_number(token), _parse_page_number(token) + 1)
        for number in numbers:
            if number > page_count:
                raise ValidationError(
                    ErrorCode.VALIDATION_FAILED,
                    f"Page {number} is out of range for PDF with {page_count} pages",
                )
            index = number - 1
            if index not in seen:
                selected.append(index)
                seen.add(index)
    if not selected:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "No pages selected")
    return selected


def page_selection_metadata(
    page_count: int, indexes: list[int], pages: str | None
) -> dict[str, object]:
    return {
        "page_count": page_count,
        "selected_page_count": len(indexes),
        "selected_pages": [index + 1 for index in indexes],
        "page_range": pages,
        "partial": len(indexes) != page_count,
    }


def _parse_page_number(value: str) -> int:
    try:
        number = int(value.strip())
    except ValueError as exc:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, f"Invalid page number: {value}") from exc
    if number < 1:
        raise ValidationError(ErrorCode.VALIDATION_FAILED, "Page numbers start at 1")
    return number
