from __future__ import annotations

from pathlib import Path
from typing import Any

from docrt.docx_styles import is_heading_style, paragraph_style_name
from docrt.paths import ensure_unlocked_for_read, validate_input_path


def read_docx(path: str | Path) -> dict[str, object]:
    input_path = validate_input_path(path, {".docx"})
    ensure_unlocked_for_read(input_path)
    try:
        from docx import Document
    except Exception as exc:
        raise RuntimeError("python-docx is unavailable") from exc

    document = Document(str(input_path))
    content_blocks: list[dict[str, object]] = []
    for index, paragraph in enumerate(document.paragraphs):
        style_name = paragraph_style_name(paragraph)
        content_blocks.append(
            {
                "type": "heading" if is_heading_style(style_name) else "paragraph",
                "text": paragraph.text,
                "location": {"paragraph_index": index},
                "style": style_name,
                "is_heading": is_heading_style(style_name),
            }
        )

    tables: list[dict[str, object]] = []
    for table_index, table in enumerate(document.tables):
        rows = []
        for row_index, row in enumerate(table.rows):
            cells = []
            for column_index, cell in enumerate(row.cells):
                text = cell.text
                cells.append(
                    {
                        "text": text,
                        "location": {
                            "table_index": table_index,
                            "row_index": row_index,
                            "column_index": column_index,
                        },
                    }
                )
                content_blocks.append(
                    {
                        "type": "table_cell",
                        "text": text,
                        "location": {
                            "table_index": table_index,
                            "row_index": row_index,
                            "column_index": column_index,
                        },
                    }
                )
            rows.append(cells)
        tables.append({"table_index": table_index, "rows": rows})

    return {
        "document_type": "docx",
        "path": str(input_path),
        "metadata": {
            "paragraph_count": len(document.paragraphs),
            "table_count": len(document.tables),
        },
        "content_blocks": content_blocks,
        "tables": tables,
        "warnings": [],
    }


def read_pdf(path: str | Path) -> dict[str, object]:
    input_path = validate_input_path(path, {".pdf"})
    ensure_unlocked_for_read(input_path)
    try:
        import fitz
    except Exception as exc:
        raise RuntimeError("PyMuPDF is unavailable") from exc

    document = fitz.open(str(input_path))
    try:
        content_blocks: list[dict[str, object]] = []
        pages: list[dict[str, Any]] = []
        total_text_chars = 0
        for index, page in enumerate(document):
            text = page.get_text("text")
            total_text_chars += len(text)
            rect = page.rect
            page_number = index + 1
            pages.append(
                {
                    "page_number": page_number,
                    "width": rect.width,
                    "height": rect.height,
                    "text_chars": len(text),
                }
            )
            content_blocks.append(
                {
                    "type": "page_text",
                    "text": text,
                    "location": {
                        "page_number": page_number,
                        "width": rect.width,
                        "height": rect.height,
                    },
                }
            )
        warnings = [] if total_text_chars else ["PDF has no text layer; OCR is not supported."]
        return {
            "document_type": "pdf",
            "path": str(input_path),
            "metadata": {
                "page_count": document.page_count,
                "pdf_metadata": dict(document.metadata or {}),
                "has_text_layer": total_text_chars > 0,
                "pages": pages,
            },
            "content_blocks": content_blocks,
            "tables": [],
            "warnings": warnings,
        }
    finally:
        document.close()


def read_xlsx(path: str | Path) -> dict[str, object]:
    input_path = validate_input_path(path, {".xlsx"})
    ensure_unlocked_for_read(input_path)
    try:
        import openpyxl
    except Exception as exc:
        raise RuntimeError("openpyxl is unavailable") from exc

    workbook = openpyxl.load_workbook(str(input_path), data_only=False, read_only=False)
    try:
        content_blocks: list[dict[str, object]] = []
        tables: list[dict[str, object]] = []
        sheets: list[dict[str, object]] = []
        for sheet in workbook.worksheets:
            rows = []
            max_row = min(sheet.max_row or 0, 20)
            max_col = min(sheet.max_column or 0, 20)
            for row in sheet.iter_rows(
                min_row=1,
                max_row=max_row,
                min_col=1,
                max_col=max_col,
            ):
                row_values = []
                for cell in row:
                    value = cell.value
                    row_values.append(value)
                    if value is not None:
                        content_blocks.append(
                            {
                                "type": "cell",
                                "text": str(value),
                                "location": {
                                    "sheet": sheet.title,
                                    "cell": cell.coordinate,
                                    "row": cell.row,
                                    "column": cell.column,
                                },
                            }
                        )
                rows.append(row_values)
            end_cell = sheet.cell(max_row, max_col).coordinate if max_row and max_col else "A1"
            tables.append({"sheet": sheet.title, "range": f"A1:{end_cell}", "rows": rows})
            sheets.append(
                {
                    "name": sheet.title,
                    "max_row": sheet.max_row,
                    "max_column": sheet.max_column,
                    "merged_cells": [str(rng) for rng in sheet.merged_cells.ranges],
                }
            )

        return {
            "document_type": "xlsx",
            "path": str(input_path),
            "metadata": {
                "sheet_count": len(workbook.worksheets),
                "sheets": sheets,
            },
            "content_blocks": content_blocks,
            "tables": tables,
            "warnings": [],
        }
    finally:
        workbook.close()
