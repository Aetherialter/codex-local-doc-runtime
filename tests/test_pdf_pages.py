from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from docrt.paths import ValidationError
from docrt.pdf_ops import render_pdf, search_pdf
from docrt.pdf_pages import selected_page_indexes
from docrt.read_ops import read_pdf


def _make_pdf(path: Path) -> None:
    document = fitz.open()
    for index in range(3):
        page = document.new_page()
        page.insert_text((72, 72), f"page {index + 1} marker")
    document.save(path)
    document.close()


def test_selected_page_indexes_parses_ranges() -> None:
    assert selected_page_indexes(5, "1,3-4,3") == [0, 2, 3]


def test_selected_page_indexes_rejects_out_of_range() -> None:
    with pytest.raises(ValidationError):
        selected_page_indexes(2, "3")


def test_read_pdf_limits_pages(tmp_path: Path) -> None:
    path = tmp_path / "sample.pdf"
    _make_pdf(path)

    result = read_pdf(path, pages="2-3")

    assert result["metadata"]["page_selection"]["selected_pages"] == [2, 3]
    assert len(result["content_blocks"]) == 2
    assert "page 1 marker" not in result["content_blocks"][0]["text"]


def test_search_pdf_limits_pages(tmp_path: Path) -> None:
    path = tmp_path / "sample.pdf"
    _make_pdf(path)

    result = search_pdf(path, "marker", pages="1")

    assert result["page_selection"]["selected_pages"] == [1]
    assert result["count"] == 1


def test_render_pdf_limits_pages(tmp_path: Path) -> None:
    path = tmp_path / "sample.pdf"
    output_dir = tmp_path / "rendered"
    _make_pdf(path)

    result = render_pdf(path, output_dir, pages="3")

    assert result["page_selection"]["selected_pages"] == [3]
    assert len(result["pages"]) == 1
    assert Path(result["pages"][0]).name == "page-0003.png"
