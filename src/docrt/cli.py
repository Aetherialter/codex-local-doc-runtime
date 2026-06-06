from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from docrt.agent import agent_config
from docrt.cache_ops import (
    batch_fingerprint,
    batch_inspect,
    batch_read,
    cache_read,
    fingerprint_file,
    index,
    search,
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
from docrt.config import Config
from docrt.config_cli import config_init, config_set, config_show
from docrt.doctor import doctor_report
from docrt.docx_ops import inspect_docx
from docrt.jobs import job_status, start_job
from docrt.jsonutil import dump_file
from docrt.log_analysis import analyze_logs, recent_errors
from docrt.maintenance import maintenance_report
from docrt.office_convert import docx_to_pdf, xlsx_to_pdf
from docrt.patch_ops import patch_docx, patch_xlsx
from docrt.paths import (
    default_inspect_output,
    default_pdf_output,
    default_render_output_dir,
    normalize_path,
)
from docrt.pdf_annotate import annotate_pdf
from docrt.pdf_ops import inspect_pdf, render_pdf, search_pdf
from docrt.read_ops import read_docx, read_pdf, read_xlsx
from docrt.repair_plan import repair_plan
from docrt.runner import run_operation
from docrt.schema_ops import validate_patch, validate_result, validate_task
from docrt.storage_ops import clean, storage_report
from docrt.task_ops import explain_task_manifest, run_task_manifest
from docrt.verify_ops import compare_docx, compare_xlsx, verify_docx, verify_xlsx
from docrt.version_info import version_report
from docrt.xlsx_ops import inspect_xlsx

app = typer.Typer(no_args_is_help=True, add_completion=False)
config_app = typer.Typer(no_args_is_help=True, add_completion=False)
app.add_typer(config_app, name="config")


def _config(poppler_path: str | None, timeout: int | None, force_kill_office: bool) -> Config:
    return load_cli_config(poppler_path, timeout, force_kill_office)


def _emit(result) -> None:
    emit_result(result)


@app.command()
def version(
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "version",
        lambda _run_id, _cfg, _logger: version_report(),
        config=config,
        backend="version",
    )
    _emit(result)


@app.command()
def doctor(
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
    office_smoke: Annotated[bool, typer.Option("--office-smoke")] = False,
    agent: Annotated[bool, typer.Option("--agent")] = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "doctor",
        lambda _run_id, cfg, _logger: doctor_report(cfg, office_smoke=office_smoke, agent=agent),
        config=config,
        backend="doctor",
    )
    _emit(result)


@app.command("agent-config")
def agent_config_cmd(
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "agent-config",
        lambda _run_id, cfg, _logger: agent_config(cfg),
        config=config,
        backend="agent",
    )
    _emit(result)


@app.command("inspect-docx")
def inspect_docx_cmd(
    path: Path,
    output: OutputOpt = None,
    pages: Annotated[str | None, typer.Option("--pages")] = None,
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
    pages: Annotated[str | None, typer.Option("--pages")] = None,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(path)
    output_path = normalize_path(output) if output else None

    def handler(_run_id, _cfg, _logger):
        data = read_pdf(input_path, pages=pages)
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
    pages: Annotated[str | None, typer.Option("--pages")] = None,
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
        lambda _run_id, _cfg, _logger: render_pdf(input_path, target_dir, pages=pages),
        config=config,
        input_path=input_path,
        output_path=target_dir,
        backend="pymupdf",
    )
    _emit(result)


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
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(path)
    output_path = normalize_path(output) if output else None

    def handler(_run_id, _cfg, _logger):
        data = search_pdf(input_path, query, pages=pages)
        if output_path:
            dump_file(output_path, data)
        return data

    result = run_operation(
        "search-pdf",
        handler,
        config=config,
        input_path=input_path,
        output_path=output_path,
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
    dry_run: DryRunOpt = False,
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
        lambda _run_id, _cfg, _logger: patch_docx(
            input_path, patch_path, output_path, dry_run=dry_run
        ),
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
    dry_run: DryRunOpt = False,
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
        lambda _run_id, _cfg, _logger: patch_xlsx(
            input_path, patch_path, output_path, dry_run=dry_run
        ),
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
    expect: ExpectOpt = None,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    before_path = normalize_path(before)
    after_path = normalize_path(after)
    expect_path = normalize_path(expect) if expect else None
    result = run_operation(
        "verify-docx",
        lambda _run_id, _cfg, _logger: verify_docx(before_path, after_path, expect_path),
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
    expect: ExpectOpt = None,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    before_path = normalize_path(before)
    after_path = normalize_path(after)
    expect_path = normalize_path(expect) if expect else None
    result = run_operation(
        "verify-xlsx",
        lambda _run_id, _cfg, _logger: verify_xlsx(before_path, after_path, expect_path),
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


@app.command("explain-task")
def explain_task_cmd(
    task: Path,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    task_path = normalize_path(task)
    result = run_operation(
        "explain-task",
        lambda _run_id, _cfg, _logger: explain_task_manifest(task_path),
        config=config,
        input_path=task_path,
        backend="task-manifest",
    )
    _emit(result)


@app.command("compare-docx")
def compare_docx_cmd(
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
        "compare-docx",
        lambda _run_id, _cfg, _logger: compare_docx(before_path, after_path),
        config=config,
        input_path=before_path,
        output_path=after_path,
        backend="python-docx",
    )
    _emit(result)


@app.command("compare-xlsx")
def compare_xlsx_cmd(
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
        "compare-xlsx",
        lambda _run_id, _cfg, _logger: compare_xlsx(before_path, after_path),
        config=config,
        input_path=before_path,
        output_path=after_path,
        backend="openpyxl",
    )
    _emit(result)


@app.command("validate-patch")
def validate_patch_cmd(
    path: Path,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(path)
    result = run_operation(
        "validate-patch",
        lambda _run_id, _cfg, _logger: validate_patch(input_path),
        config=config,
        input_path=input_path,
        backend="jsonschema",
    )
    _emit(result)


@app.command("validate-task")
def validate_task_cmd(
    path: Path,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(path)
    result = run_operation(
        "validate-task",
        lambda _run_id, _cfg, _logger: validate_task(input_path),
        config=config,
        input_path=input_path,
        backend="jsonschema",
    )
    _emit(result)


@app.command("validate-result")
def validate_result_cmd(
    path: Path,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(path)
    result = run_operation(
        "validate-result",
        lambda _run_id, _cfg, _logger: validate_result(input_path),
        config=config,
        input_path=input_path,
        backend="jsonschema",
    )
    _emit(result)


@app.command("annotate-pdf")
def annotate_pdf_cmd(
    input: Path,
    annotations: Path,
    output: Path,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(input)
    annotations_path = normalize_path(annotations)
    output_path = normalize_path(output)
    result = run_operation(
        "annotate-pdf",
        lambda _run_id, _cfg, _logger: annotate_pdf(input_path, annotations_path, output_path),
        config=config,
        input_path=input_path,
        output_path=output_path,
        backend="pymupdf",
    )
    _emit(result)


@app.command("fingerprint")
def fingerprint_cmd(
    path: Path,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(path)
    result = run_operation(
        "fingerprint",
        lambda _run_id, _cfg, _logger: fingerprint_file(input_path),
        config=config,
        input_path=input_path,
        backend="core-bridge",
    )
    _emit(result)


@app.command("batch-fingerprint")
def batch_fingerprint_cmd(
    paths: list[Path],
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "batch-fingerprint",
        lambda _run_id, _cfg, _logger: batch_fingerprint(paths),
        config=config,
        backend="core-bridge",
    )
    _emit(result)


@app.command("cache-read")
def cache_read_cmd(
    path: Path,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    input_path = normalize_path(path)
    result = run_operation(
        "cache-read",
        lambda _run_id, cfg, _logger: cache_read(input_path, cfg),
        config=config,
        input_path=input_path,
        backend="core-bridge",
    )
    _emit(result)


@app.command("batch-read")
def batch_read_cmd(
    paths: list[Path],
    use_cache: Annotated[bool, typer.Option("--use-cache")] = False,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "batch-read",
        lambda _run_id, cfg, _logger: batch_read(paths, cfg, use_cache=use_cache),
        config=config,
        backend="core-bridge",
    )
    _emit(result)


@app.command("batch-inspect")
def batch_inspect_cmd(
    paths: list[Path],
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "batch-inspect",
        lambda _run_id, _cfg, _logger: batch_inspect(paths),
        config=config,
        backend="inspect",
    )
    _emit(result)


@app.command("index")
def index_cmd(
    paths: list[Path],
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "index",
        lambda _run_id, cfg, _logger: index(paths, cfg),
        config=config,
        backend="core-bridge",
    )
    _emit(result)


@app.command("search")
def search_cmd(
    query: str,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "search",
        lambda _run_id, cfg, _logger: search(query, cfg),
        config=config,
        backend="core-bridge",
    )
    _emit(result)


@app.command("storage-report")
def storage_report_cmd(
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "storage-report",
        lambda _run_id, cfg, _logger: storage_report(cfg),
        config=config,
        backend="python",
    )
    _emit(result)


@app.command("clean")
def clean_cmd(
    older_than: Annotated[int | None, typer.Option("--older-than", min=0)] = None,
    retention: Annotated[bool, typer.Option("--retention")] = False,
    yes: Annotated[bool, typer.Option("--yes")] = False,
    verbose: Annotated[bool, typer.Option("--verbose")] = False,
    logs: Annotated[bool, typer.Option("--logs")] = False,
    outputs: Annotated[bool, typer.Option("--outputs")] = False,
    work: Annotated[bool, typer.Option("--work")] = False,
    diagnostics: Annotated[bool, typer.Option("--diagnostics")] = False,
    cache: Annotated[bool, typer.Option("--cache")] = False,
    dist: Annotated[bool, typer.Option("--dist")] = False,
    all_targets: Annotated[bool, typer.Option("--all")] = False,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "clean",
        lambda _run_id, cfg, _logger: clean(
            cfg,
            older_than_days=older_than,
            yes=yes,
            include_files=verbose,
            retention=retention,
            logs=logs,
            outputs=outputs,
            work=work,
            diagnostics=diagnostics,
            cache=cache,
            dist=dist,
            all_targets=all_targets,
        ),
        config=config,
        backend="python",
    )
    _emit(result)


@app.command("analyze-logs")
def analyze_logs_cmd(
    days: Annotated[int, typer.Option("--days", min=1)] = 7,
    limit: Annotated[int, typer.Option("--limit", min=0)] = 200,
    include_events: Annotated[bool, typer.Option("--include-events")] = False,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "analyze-logs",
        lambda _run_id, cfg, _logger: analyze_logs(
            cfg,
            days=days,
            limit=limit,
            include_events=include_events,
        ),
        config=config,
        backend="log-analysis",
    )
    _emit(result)


@app.command("recent-errors")
def recent_errors_cmd(
    limit: Annotated[int, typer.Option("--limit", min=0)] = 20,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "recent-errors",
        lambda _run_id, cfg, _logger: recent_errors(cfg, limit=limit),
        config=config,
        backend="log-analysis",
    )
    _emit(result)


@app.command("repair-plan")
def repair_plan_cmd(
    days: Annotated[int, typer.Option("--days", min=1)] = 30,
    limit: Annotated[int, typer.Option("--limit", min=0)] = 200,
    no_persist: Annotated[bool, typer.Option("--no-persist")] = False,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "repair-plan",
        lambda _run_id, cfg, _logger: repair_plan(
            cfg,
            days=days,
            limit=limit,
            persist=not no_persist,
        ),
        config=config,
        backend="repair-plan",
    )
    _emit(result)


@app.command("maintenance")
def maintenance_cmd(
    analyze_days: Annotated[int, typer.Option("--analyze-days", min=1)] = 7,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "maintenance",
        lambda _run_id, cfg, _logger: maintenance_report(cfg, analyze_days=analyze_days),
        config=config,
        backend="maintenance",
    )
    _emit(result)


@app.command("job-start")
def job_start_cmd(
    task: str,
    days: Annotated[int, typer.Option("--days", min=1)] = 7,
    yes: Annotated[bool, typer.Option("--yes")] = False,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    args = ["--days", str(days)]
    if yes:
        args.append("--yes")
    result = run_operation(
        "job-start",
        lambda _run_id, cfg, _logger: start_job(cfg, task, args=args),
        config=config,
        backend="jobs",
    )
    _emit(result)


@app.command("job-status")
def job_status_cmd(
    job_id: str,
    poppler_path: PopplerOpt = None,
    timeout: TimeoutOpt = None,
    force_kill_office: ForceKillOpt = False,
) -> None:
    config = _config(poppler_path, timeout, force_kill_office)
    result = run_operation(
        "job-status",
        lambda _run_id, cfg, _logger: job_status(cfg, job_id),
        config=config,
        backend="jobs",
    )
    _emit(result)


@config_app.command("init")
def config_init_cmd(force: Annotated[bool, typer.Option("--force")] = False) -> None:
    config = Config.load()
    result = run_operation(
        "config-init",
        lambda _run_id, _cfg, _logger: config_init(force=force),
        config=config,
        backend="config",
    )
    _emit(result)


@config_app.command("show")
def config_show_cmd() -> None:
    config = Config.load()
    result = run_operation(
        "config-show",
        lambda _run_id, cfg, _logger: config_show(cfg),
        config=config,
        backend="config",
    )
    _emit(result)


@config_app.command("set")
def config_set_cmd(key: str, value: str) -> None:
    config = Config.load()
    result = run_operation(
        "config-set",
        lambda _run_id, _cfg, _logger: config_set(key, value),
        config=config,
        backend="config",
    )
    _emit(result)
