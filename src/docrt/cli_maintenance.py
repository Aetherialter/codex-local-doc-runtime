from __future__ import annotations

from typing import Annotated

import typer

from docrt.cli_support import ForceKillOpt, PopplerOpt, TimeoutOpt, emit_result, load_cli_config
from docrt.jobs import job_status, start_job
from docrt.log_analysis import analyze_logs, recent_errors
from docrt.maintenance import maintenance_report
from docrt.repair_plan import repair_plan
from docrt.runner import run_operation
from docrt.storage_ops import clean, storage_report


def register(app: typer.Typer) -> None:
    @app.command("storage-report")
    def storage_report_cmd(
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        result = run_operation(
            "storage-report",
            lambda _run_id, cfg, _logger: storage_report(cfg),
            config=config,
            backend="python",
        )
        emit_result(result)

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
        config = load_cli_config(poppler_path, timeout, force_kill_office)
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
        emit_result(result)

    @app.command("analyze-logs")
    def analyze_logs_cmd(
        days: Annotated[int, typer.Option("--days", min=1)] = 7,
        limit: Annotated[int, typer.Option("--limit", min=0)] = 200,
        include_events: Annotated[bool, typer.Option("--include-events")] = False,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
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
        emit_result(result)

    @app.command("recent-errors")
    def recent_errors_cmd(
        limit: Annotated[int, typer.Option("--limit", min=0)] = 20,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        result = run_operation(
            "recent-errors",
            lambda _run_id, cfg, _logger: recent_errors(cfg, limit=limit),
            config=config,
            backend="log-analysis",
        )
        emit_result(result)

    @app.command("repair-plan")
    def repair_plan_cmd(
        days: Annotated[int, typer.Option("--days", min=1)] = 30,
        limit: Annotated[int, typer.Option("--limit", min=0)] = 200,
        no_persist: Annotated[bool, typer.Option("--no-persist")] = False,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
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
        emit_result(result)

    @app.command("maintenance")
    def maintenance_cmd(
        analyze_days: Annotated[int, typer.Option("--analyze-days", min=1)] = 7,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        result = run_operation(
            "maintenance",
            lambda _run_id, cfg, _logger: maintenance_report(cfg, analyze_days=analyze_days),
            config=config,
            backend="maintenance",
        )
        emit_result(result)

    @app.command("job-start")
    def job_start_cmd(
        task: str,
        days: Annotated[int, typer.Option("--days", min=1)] = 7,
        yes: Annotated[bool, typer.Option("--yes")] = False,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        args = ["--days", str(days)]
        if yes:
            args.append("--yes")
        result = run_operation(
            "job-start",
            lambda _run_id, cfg, _logger: start_job(cfg, task, args=args),
            config=config,
            backend="jobs",
        )
        emit_result(result)

    @app.command("job-status")
    def job_status_cmd(
        job_id: str,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        result = run_operation(
            "job-status",
            lambda _run_id, cfg, _logger: job_status(cfg, job_id),
            config=config,
            backend="jobs",
        )
        emit_result(result)
