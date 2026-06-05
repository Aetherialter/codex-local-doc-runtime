from __future__ import annotations

from pathlib import Path

from docrt.paths import ensure_unlocked_for_read, validate_input_path, validate_output_path


def inspect_pdf(path: str | Path) -> dict[str, object]:
    input_path = validate_input_path(path, {".pdf"})
    ensure_unlocked_for_read(input_path)
    try:
        import fitz
    except Exception as exc:
        raise RuntimeError("PyMuPDF is unavailable") from exc

    document = fitz.open(str(input_path))
    try:
        pages = []
        total_text_chars = 0
        for index, page in enumerate(document):
            text = page.get_text("text")
            total_text_chars += len(text)
            rect = page.rect
            pages.append(
                {
                    "page_number": index + 1,
                    "width": rect.width,
                    "height": rect.height,
                    "text_chars": len(text),
                }
            )
        return {
            "path": str(input_path),
            "page_count": document.page_count,
            "metadata": dict(document.metadata or {}),
            "has_text_layer": total_text_chars > 0,
            "pages": pages,
        }
    finally:
        document.close()


def render_pdf(path: str | Path, output_dir: str | Path, *, dpi: int = 144) -> dict[str, object]:
    input_path = validate_input_path(path, {".pdf"})
    ensure_unlocked_for_read(input_path)
    normalized_output = validate_output_path(Path(output_dir) / ".docrt-write-test").parent
    normalized_output.mkdir(parents=True, exist_ok=True)
    try:
        import fitz
    except Exception as exc:
        raise RuntimeError("PyMuPDF is unavailable") from exc

    document = fitz.open(str(input_path))
    written: list[str] = []
    try:
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        for index, page in enumerate(document):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            output = normalized_output / f"page-{index + 1:04d}.png"
            pixmap.save(str(output))
            written.append(str(output))
        return {"path": str(input_path), "output_dir": str(normalized_output), "pages": written}
    finally:
        document.close()


def search_pdf(path: str | Path, query: str, *, preview_size: int = 120) -> dict[str, object]:
    input_path = validate_input_path(path, {".pdf"})
    ensure_unlocked_for_read(input_path)
    if not query:
        raise ValueError("query must not be empty")
    try:
        import fitz
    except Exception as exc:
        raise RuntimeError("PyMuPDF is unavailable") from exc

    document = fitz.open(str(input_path))
    matches: list[dict[str, object]] = []
    try:
        normalized_query = query.casefold()
        for index, page in enumerate(document):
            text = page.get_text("text")
            normalized_text = text.casefold()
            start = 0
            page_matches = []
            while True:
                found = normalized_text.find(normalized_query, start)
                if found < 0:
                    break
                page_matches.append(
                    {
                        "offset": found,
                        "preview": _preview(text, found, len(query), preview_size),
                    }
                )
                start = found + max(len(query), 1)
            if page_matches:
                matches.append(
                    {
                        "page_number": index + 1,
                        "count": len(page_matches),
                        "matches": page_matches,
                    }
                )
        return {
            "path": str(input_path),
            "query": query,
            "page_count": document.page_count,
            "count": sum(int(page["count"]) for page in matches),
            "matches": matches,
        }
    finally:
        document.close()


def _preview(text: str, offset: int, length: int, preview_size: int) -> str:
    half = max(preview_size, 1) // 2
    start = max(offset - half, 0)
    end = min(offset + length + half, len(text))
    return text[start:end].replace("\r", " ").replace("\n", " ")
