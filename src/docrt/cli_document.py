from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from docrt.api import (
    annotate_document,
    compare_documents,
    export_pdf,
    inspect_document,
    patch_document,
    read_document,
    render_document,
    search_document,
    verify_document,
)
from docrt.cli_support import (
    DryRunOpt,
    ExpectOpt,
    ForceKillOpt,
    OutputOpt,
    PopplerOpt,
    TimeoutOpt,
    emit_result,
    load_cli_config,
)
from docrt.jsonutil import dump_file
from docrt.paths import (
    default_inspect_output,
    default_pdf_output,
    default_render_output_dir,
    normalize_path,
)
from docrt.runner import run_operation


def register(app: typer.Typer) -> None:
    @app.command("inspect-docx")
    def inspect_docx_cmd(
        path: Path,
        output: OutputOpt = None,
        pages: Annotated[str | None, typer.Option("--pages")] = None,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        _ = pages
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(path)
        output_path = (
            normalize_path(output)
            if output
            else default_inspect_output(input_path, config.outputs_path)
        )

        def handler(_run_id, _cfg, _logger):
            data = inspect_document(input_path)
            dump_file(output_path, data)
            return data

        result = run_operation(
            "inspect-docx",
            handler,
            config=config,
            input_path=input_path,
            output_path=output_path,
            backend="native",
        )
        emit_result(result)

    @app.command("read-docx")
    def read_docx_cmd(
        path: Path,
        output: OutputOpt = None,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(path)
        output_path = normalize_path(output) if output else None

        def handler(_run_id, _cfg, _logger):
            data = read_document(input_path)
            if output_path:
                dump_file(output_path, data)
            return data

        result = run_operation(
            "read-docx",
            handler,
            config=config,
            input_path=input_path,
            output_path=output_path,
            backend="native",
        )
        emit_result(result)

    @app.command("docx-to-pdf")
    def docx_to_pdf_cmd(
        input: Path,
        output: Annotated[Path | None, typer.Argument()] = None,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(input)
        output_path = (
            normalize_path(output)
            if output
            else default_pdf_output(input_path, config.outputs_path)
        )
        result = run_operation(
            "docx-to-pdf",
            lambda run_id, cfg, _logger: export_pdf(input_path, output_path, cfg, run_id),
            config=config,
            input_path=input_path,
            output_path=output_path,
            backend="office_com",
        )
        emit_result(result)

    @app.command("inspect-pdf")
    def inspect_pdf_cmd(
        path: Path,
        output: OutputOpt = None,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(path)
        output_path = (
            normalize_path(output)
            if output
            else default_inspect_output(input_path, config.outputs_path)
        )

        def handler(_run_id, _cfg, _logger):
            data = inspect_document(input_path)
            dump_file(output_path, data)
            return data

        result = run_operation(
            "inspect-pdf",
            handler,
            config=config,
            input_path=input_path,
            output_path=output_path,
            backend="native",
        )
        emit_result(result)

    @app.command("read-pdf")
    def read_pdf_cmd(
        path: Path,
        output: OutputOpt = None,
        pages: Annotated[str | None, typer.Option("--pages")] = None,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(path)
        output_path = normalize_path(output) if output else None

        def handler(_run_id, _cfg, _logger):
            data = read_document(input_path, pages=pages)
            if output_path:
                dump_file(output_path, data)
            return data

        result = run_operation(
            "read-pdf",
            handler,
            config=config,
            input_path=input_path,
            output_path=output_path,
            backend="native",
        )
        emit_result(result)

    @app.command("render-pdf")
    def render_pdf_cmd(
        input: Path,
        output_dir: Annotated[Path | None, typer.Argument()] = None,
        pages: Annotated[str | None, typer.Option("--pages")] = None,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(input)
        target_dir = (
            normalize_path(output_dir)
            if output_dir
            else default_render_output_dir(input_path, config.outputs_path)
        )
        result = run_operation(
            "render-pdf",
            lambda _run_id, _cfg, _logger: render_document(input_path, target_dir, pages=pages),
            config=config,
            input_path=input_path,
            output_path=target_dir,
            backend="native",
        )
        emit_result(result)

    @app.command("search-pdf")
    def search_pdf_cmd(
        path: Path,
        query: str,
        output: OutputOpt = None,
        pages: Annotated[str | None, typer.Option("--pages")] = None,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(path)
        output_path = normalize_path(output) if output else None

        def handler(_run_id, _cfg, _logger):
            data = search_document(input_path, query, pages=pages)
            if output_path:
                dump_file(output_path, data)
            return data

        result = run_operation(
            "search-pdf",
            handler,
            config=config,
            input_path=input_path,
            output_path=output_path,
            backend="native",
        )
        emit_result(result)

    @app.command("inspect-xlsx")
    def inspect_xlsx_cmd(
        path: Path,
        output: OutputOpt = None,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(path)
        output_path = (
            normalize_path(output)
            if output
            else default_inspect_output(input_path, config.outputs_path)
        )

        def handler(_run_id, _cfg, _logger):
            data = inspect_document(input_path)
            dump_file(output_path, data)
            return data

        result = run_operation(
            "inspect-xlsx",
            handler,
            config=config,
            input_path=input_path,
            output_path=output_path,
            backend="native",
        )
        emit_result(result)

    @app.command("read-xlsx")
    def read_xlsx_cmd(
        path: Path,
        output: OutputOpt = None,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(path)
        output_path = normalize_path(output) if output else None

        def handler(_run_id, _cfg, _logger):
            data = read_document(input_path)
            if output_path:
                dump_file(output_path, data)
            return data

        result = run_operation(
            "read-xlsx",
            handler,
            config=config,
            input_path=input_path,
            output_path=output_path,
            backend="native",
        )
        emit_result(result)

    @app.command("xlsx-to-pdf")
    def xlsx_to_pdf_cmd(
        input: Path,
        output: Annotated[Path | None, typer.Argument()] = None,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(input)
        output_path = (
            normalize_path(output)
            if output
            else default_pdf_output(input_path, config.outputs_path)
        )
        result = run_operation(
            "xlsx-to-pdf",
            lambda run_id, cfg, _logger: export_pdf(input_path, output_path, cfg, run_id),
            config=config,
            input_path=input_path,
            output_path=output_path,
            backend="office_com",
        )
        emit_result(result)

    @app.command("patch-docx")
    def patch_docx_cmd(
        input: Path,
        patch: Path,
        output: Path,
        dry_run: DryRunOpt = False,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(input)
        patch_path = normalize_path(patch)
        output_path = normalize_path(output)
        result = run_operation(
            "patch-docx",
            lambda _run_id, _cfg, _logger: patch_document(
                input_path, patch_path, output_path, dry_run=dry_run
            ),
            config=config,
            input_path=input_path,
            output_path=output_path,
            backend="native",
        )
        emit_result(result)

    @app.command("patch-xlsx")
    def patch_xlsx_cmd(
        input: Path,
        patch: Path,
        output: Path,
        dry_run: DryRunOpt = False,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(input)
        patch_path = normalize_path(patch)
        output_path = normalize_path(output)
        result = run_operation(
            "patch-xlsx",
            lambda _run_id, _cfg, _logger: patch_document(
                input_path, patch_path, output_path, dry_run=dry_run
            ),
            config=config,
            input_path=input_path,
            output_path=output_path,
            backend="native",
        )
        emit_result(result)

    @app.command("verify-docx")
    def verify_docx_cmd(
        before: Path,
        after: Path,
        expect: ExpectOpt = None,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        before_path = normalize_path(before)
        after_path = normalize_path(after)
        expect_path = normalize_path(expect) if expect else None
        result = run_operation(
            "verify-docx",
            lambda _run_id, _cfg, _logger: verify_document(
                before_path, after_path, expect_path=expect_path
            ),
            config=config,
            input_path=before_path,
            output_path=after_path,
            backend="native",
        )
        emit_result(result)

    @app.command("verify-xlsx")
    def verify_xlsx_cmd(
        before: Path,
        after: Path,
        expect: ExpectOpt = None,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        before_path = normalize_path(before)
        after_path = normalize_path(after)
        expect_path = normalize_path(expect) if expect else None
        result = run_operation(
            "verify-xlsx",
            lambda _run_id, _cfg, _logger: verify_document(
                before_path, after_path, expect_path=expect_path
            ),
            config=config,
            input_path=before_path,
            output_path=after_path,
            backend="native",
        )
        emit_result(result)

    @app.command("compare-docx")
    def compare_docx_cmd(
        before: Path,
        after: Path,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        before_path = normalize_path(before)
        after_path = normalize_path(after)
        result = run_operation(
            "compare-docx",
            lambda _run_id, _cfg, _logger: compare_documents(before_path, after_path),
            config=config,
            input_path=before_path,
            output_path=after_path,
            backend="native",
        )
        emit_result(result)

    @app.command("compare-xlsx")
    def compare_xlsx_cmd(
        before: Path,
        after: Path,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        before_path = normalize_path(before)
        after_path = normalize_path(after)
        result = run_operation(
            "compare-xlsx",
            lambda _run_id, _cfg, _logger: compare_documents(before_path, after_path),
            config=config,
            input_path=before_path,
            output_path=after_path,
            backend="native",
        )
        emit_result(result)

    @app.command("annotate-pdf")
    def annotate_pdf_cmd(
        input: Path,
        annotations: Path,
        output: Path,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(input)
        annotations_path = normalize_path(annotations)
        output_path = normalize_path(output)
        result = run_operation(
            "annotate-pdf",
            lambda _run_id, _cfg, _logger: annotate_document(
                input_path, annotations_path, output_path
            ),
            config=config,
            input_path=input_path,
            output_path=output_path,
            backend="native",
        )
        emit_result(result)
