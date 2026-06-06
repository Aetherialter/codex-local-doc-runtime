from __future__ import annotations

from pathlib import Path

from docrt.config import Config
from docrt.docx_ops import inspect_docx
from docrt.models import ErrorCode
from docrt.office_convert import docx_to_pdf, xlsx_to_pdf
from docrt.patch_ops import patch_docx, patch_xlsx
from docrt.paths import ValidationError
from docrt.pdf_annotate import annotate_pdf
from docrt.pdf_ops import inspect_pdf, render_pdf, search_pdf
from docrt.read_ops import read_docx, read_pdf, read_xlsx
from docrt.runtime_env import assert_mainline_runtime_for_path, confirmed_mainline_runtime
from docrt.verify_ops import compare_docx, compare_xlsx, verify_docx, verify_xlsx
from docrt.xlsx_ops import inspect_xlsx


def inspect_document(path: str | Path) -> dict[str, object]:
    input_path = Path(path)
    assert_mainline_runtime_for_path(input_path)
    with confirmed_mainline_runtime():
        suffix = input_path.suffix.lower()
        if suffix == ".docx":
            return inspect_docx(input_path)
        if suffix == ".pdf":
            return inspect_pdf(input_path)
        if suffix == ".xlsx":
            return inspect_xlsx(input_path)
    raise _unsupported_suffix(input_path, "inspect")


def read_document(path: str | Path, *, pages: str | None = None) -> dict[str, object]:
    input_path = Path(path)
    assert_mainline_runtime_for_path(input_path)
    with confirmed_mainline_runtime():
        suffix = input_path.suffix.lower()
        if suffix == ".docx":
            return read_docx(input_path)
        if suffix == ".pdf":
            return read_pdf(input_path, pages=pages)
        if suffix == ".xlsx":
            return read_xlsx(input_path)
    raise _unsupported_suffix(input_path, "read")


def render_document(
    path: str | Path,
    output_dir: str | Path,
    *,
    pages: str | None = None,
) -> dict[str, object]:
    input_path = Path(path)
    assert_mainline_runtime_for_path(input_path)
    with confirmed_mainline_runtime():
        if input_path.suffix.lower() == ".pdf":
            return render_pdf(input_path, Path(output_dir), pages=pages)
    raise _unsupported_suffix(input_path, "render")


def search_document(
    path: str | Path,
    query: str,
    *,
    pages: str | None = None,
) -> dict[str, object]:
    input_path = Path(path)
    assert_mainline_runtime_for_path(input_path)
    with confirmed_mainline_runtime():
        if input_path.suffix.lower() == ".pdf":
            return search_pdf(input_path, query, pages=pages)
    raise _unsupported_suffix(input_path, "search")


def annotate_document(
    input_path: str | Path,
    annotations_path: str | Path,
    output_path: str | Path,
) -> dict[str, object]:
    source = Path(input_path)
    assert_mainline_runtime_for_path(source)
    with confirmed_mainline_runtime():
        if source.suffix.lower() == ".pdf":
            return annotate_pdf(source, Path(annotations_path), Path(output_path))
    raise _unsupported_suffix(source, "annotate")


def patch_document(
    input_path: str | Path,
    patch_path: str | Path,
    output_path: str | Path,
    *,
    dry_run: bool = False,
) -> dict[str, object]:
    source = Path(input_path)
    assert_mainline_runtime_for_path(source)
    with confirmed_mainline_runtime():
        suffix = source.suffix.lower()
        if suffix == ".docx":
            return patch_docx(source, Path(patch_path), Path(output_path), dry_run=dry_run)
        if suffix == ".xlsx":
            return patch_xlsx(source, Path(patch_path), Path(output_path), dry_run=dry_run)
    raise _unsupported_suffix(source, "patch")


def verify_document(
    before_path: str | Path,
    after_path: str | Path,
    *,
    expect_path: str | Path | None = None,
) -> dict[str, object]:
    before = Path(before_path)
    assert_mainline_runtime_for_path(before)
    with confirmed_mainline_runtime():
        suffix = before.suffix.lower()
        if suffix == ".docx":
            return verify_docx(before, Path(after_path), expect_path)
        if suffix == ".xlsx":
            return verify_xlsx(before, Path(after_path), expect_path)
    raise _unsupported_suffix(before, "verify")


def compare_documents(before_path: str | Path, after_path: str | Path) -> dict[str, object]:
    before = Path(before_path)
    assert_mainline_runtime_for_path(before)
    with confirmed_mainline_runtime():
        suffix = before.suffix.lower()
        if suffix == ".docx":
            return compare_docx(before, Path(after_path))
        if suffix == ".xlsx":
            return compare_xlsx(before, Path(after_path))
    raise _unsupported_suffix(before, "compare")


def export_pdf(
    input_path: str | Path,
    output_path: str | Path | None,
    config: Config,
    run_id: str,
) -> dict[str, object]:
    source = Path(input_path)
    assert_mainline_runtime_for_path(source)
    with confirmed_mainline_runtime():
        suffix = source.suffix.lower()
        if suffix == ".docx":
            return docx_to_pdf(source, output_path, config, run_id)
        if suffix == ".xlsx":
            return xlsx_to_pdf(source, output_path, config, run_id)
    raise _unsupported_suffix(source, "export-pdf")


def _unsupported_suffix(path: Path, operation: str) -> ValidationError:
    return ValidationError(
        ErrorCode.UNSUPPORTED_FORMAT,
        f"{operation} does not support {path.suffix or '<no extension>'}.",
        context={"path": str(path), "operation": operation},
    )
