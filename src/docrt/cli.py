from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

from docrt.config import Config
from docrt.doctor import doctor_report
from docrt.docx_ops import inspect_docx
from docrt.jsonutil import dump_file, dumps
from docrt.models import exit_code_for_result
from docrt.office_convert import docx_to_pdf, xlsx_to_pdf
from docrt.patch_ops import patch_docx, patch_xlsx
from docrt.paths import (
    default_inspect_output,
    default_pdf_output,
    default_render_output_dir,
    normalize_path,
)
from docrt.pdf_ops import inspect_pdf, render_pdf
from docrt.read_ops import read_docx, read_pdf, read_xlsx
from docrt.runner import run_operation
from docrt.task_ops import run_task_manifest
from docrt.verify_ops import verify_docx, verify_xlsx
from docrt.xlsx_ops import inspect_xlsx

app = typer.Typer(no_args_is_help=True, add_completion=False)


PopplerOpt = Annotated[str | None, typer.Option("--poppler-path")]
TimeoutOpt = Annotated[int | None, typer.Option("--timeout", min=1)]
ForceKillOpt = Annotated[bool, typer.Option("--force-kill-office")]
OutputOpt = Annotated[Path | None, typer.Option("--output", "-o")]


def _config(poppler_path: str | None, timeout: int | None, force_kill_office: bool) -> Config:
    return Config.load(
        poppler_path=poppler_path,
        timeout=timeout,
        force_kill_office=force_kill_office,
    )


def _emit(result) -> None:
    text = dumps(result.to_dict(), pretty=True) + "\n"
    sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    raise typer.Exit(int(exit_code_for_result(result)))


@app.command()
def doctor(
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "doctor",
        lambda _run_id, cfg, _logger: doctor_report(cfg),
        config=config,
        backend="doctor",
    )
    _emit(result)


@app.command("inspect-docx")
def inspect_docx_cmd(
    path: Path,
    output: OutputOpt = None,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(path)
    output_path = (
        normalize_path(output)
        if output
        else default_inspect_output(input_path, config.outputs_path)
    )

    def handler(_run_id, _cfg, _logger):
        data = inspect_docx(input_path)
        dump_file(output_path, data)
        return data

    result = run_operation(
        "inspect-docx",
        handler,
        config=config,
        input_path=input_path,
        output_path=output_path,
        backend="python-docx",
    )
    _emit(result)


@app.command("read-docx")
def read_docx_cmd(
    path: Path,
    output: OutputOpt = None,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(path)
    output_path = normalize_path(output) if output else None

    def handler(_run_id, _cfg, _logger):
        data = read_docx(input_path)
        if output_path:
            dump_file(output_path, data)
        return data

    result = run_operation(
        "read-docx",
        handler,
        config=config,
        input_path=input_path,
        output_path=output_path,
        backend="python-docx",
    )
    _emit(result)


@app.command("docx-to-pdf")
def docx_to_pdf_cmd(
    input: Path,
    output: Annotated[Path | None, typer.Argument()] = None,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(input)
    output_path = (
        normalize_path(output) if output else default_pdf_output(input_path, config.outputs_path)
    )
    result = run_operation(
        "docx-to-pdf",
        lambda run_id, cfg, _logger: docx_to_pdf(input_path, output_path, cfg, run_id),
        config=config,
        input_path=input_path,
        output_path=output_path,
        backend="word-com",
    )
    _emit(result)


@app.command("inspect-pdf")
def inspect_pdf_cmd(
    path: Path,
    output: OutputOpt = None,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(path)
    output_path = (
        normalize_path(output)
        if output
        else default_inspect_output(input_path, config.outputs_path)
    )

    def handler(_run_id, _cfg, _logger):
        data = inspect_pdf(input_path)
        dump_file(output_path, data)
        return data

    result = run_operation(
        "inspect-pdf",
        handler,
        config=config,
        input_path=input_path,
        output_path=output_path,
        backend="pymupdf",
    )
    _emit(result)


@app.command("read-pdf")
def read_pdf_cmd(
    path: Path,
    output: OutputOpt = None,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(path)
    output_path = normalize_path(output) if output else None

    def handler(_run_id, _cfg, _logger):
        data = read_pdf(input_path)
        if output_path:
            dump_file(output_path, data)
        return data

    result = run_operation(
        "read-pdf",
        handler,
        config=config,
        input_path=input_path,
        output_path=output_path,
        backend="pymupdf",
    )
    _emit(result)


@app.command("render-pdf")
def render_pdf_cmd(
    input: Path,
    output_dir: Annotated[Path | None, typer.Argument()] = None,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(input)
    target_dir = (
        normalize_path(output_dir)
        if output_dir
        else default_render_output_dir(input_path, config.outputs_path)
    )
    result = run_operation(
        "render-pdf",
        lambda _run_id, _cfg, _logger: render_pdf(input_path, target_dir),
        config=config,
        input_path=input_path,
        output_path=target_dir,
        backend="pymupdf",
    )
    _emit(result)


@app.command("inspect-xlsx")
def inspect_xlsx_cmd(
    path: Path,
    output: OutputOpt = None,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(path)
    output_path = (
        normalize_path(output)
        if output
        else default_inspect_output(input_path, config.outputs_path)
    )

    def handler(_run_id, _cfg, _logger):
        data = inspect_xlsx(input_path)
        dump_file(output_path, data)
        return data

    result = run_operation(
        "inspect-xlsx",
        handler,
        config=config,
        input_path=input_path,
        output_path=output_path,
        backend="openpyxl",
    )
    _emit(result)


@app.command("read-xlsx")
def read_xlsx_cmd(
    path: Path,
    output: OutputOpt = None,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(path)
    output_path = normalize_path(output) if output else None

    def handler(_run_id, _cfg, _logger):
        data = read_xlsx(input_path)
        if output_path:
            dump_file(output_path, data)
        return data

    result = run_operation(
        "read-xlsx",
        handler,
        config=config,
        input_path=input_path,
        output_path=output_path,
        backend="openpyxl",
    )
    _emit(result)


@app.command("xlsx-to-pdf")
def xlsx_to_pdf_cmd(
    input: Path,
    output: Annotated[Path | None, typer.Argument()] = None,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(input)
    output_path = (
        normalize_path(output) if output else default_pdf_output(input_path, config.outputs_path)
    )
    result = run_operation(
        "xlsx-to-pdf",
        lambda run_id, cfg, _logger: xlsx_to_pdf(input_path, output_path, cfg, run_id),
        config=config,
        input_path=input_path,
        output_path=output_path,
        backend="excel-com",
    )
    _emit(result)


@app.command("patch-docx")
def patch_docx_cmd(
    input: Path,
    patch: Path,
    output: Path,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(input)
    patch_path = normalize_path(patch)
    output_path = normalize_path(output)
    result = run_operation(
        "patch-docx",
        lambda _run_id, _cfg, _logger: patch_docx(input_path, patch_path, output_path),
        config=config,
        input_path=input_path,
        output_path=output_path,
        backend="python-docx",
    )
    _emit(result)


@app.command("patch-xlsx")
def patch_xlsx_cmd(
    input: Path,
    patch: Path,
    output: Path,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(input)
    patch_path = normalize_path(patch)
    output_path = normalize_path(output)
    result = run_operation(
        "patch-xlsx",
        lambda _run_id, _cfg, _logger: patch_xlsx(input_path, patch_path, output_path),
        config=config,
        input_path=input_path,
        output_path=output_path,
        backend="openpyxl",
    )
    _emit(result)


@app.command("verify-docx")
def verify_docx_cmd(
    before: Path,
    after: Path,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    before_path = normalize_path(before)
    after_path = normalize_path(after)
    result = run_operation(
        "verify-docx",
        lambda _run_id, _cfg, _logger: verify_docx(before_path, after_path),
        config=config,
        input_path=before_path,
        output_path=after_path,
        backend="python-docx",
    )
    _emit(result)


@app.command("verify-xlsx")
def verify_xlsx_cmd(
    before: Path,
    after: Path,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    before_path = normalize_path(before)
    after_path = normalize_path(after)
    result = run_operation(
        "verify-xlsx",
        lambda _run_id, _cfg, _logger: verify_xlsx(before_path, after_path),
        config=config,
        input_path=before_path,
        output_path=after_path,
        backend="openpyxl",
    )
    _emit(result)


@app.command("run-task")
def run_task_cmd(
    task: Path,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    task_path = normalize_path(task)
    result = run_operation(
        "run-task",
        lambda run_id, cfg, _logger: run_task_manifest(task_path, cfg, run_id),
        config=config,
        input_path=task_path,
        backend="task-manifest",
    )
    _emit(result)
