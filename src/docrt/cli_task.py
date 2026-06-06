from __future__ import annotations

from pathlib import Path

import typer

from docrt.cli_support import ForceKillOpt, PopplerOpt, TimeoutOpt, emit_result, load_cli_config
from docrt.paths import normalize_path
from docrt.runner import run_operation
from docrt.schema_ops import validate_patch, validate_result, validate_task
from docrt.task_ops import explain_task_manifest, run_task_manifest


def register(app: typer.Typer) -> None:
    @app.command("run-task")
    def run_task_cmd(
        task: Path,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        task_path = normalize_path(task)
        result = run_operation(
            "run-task",
            lambda run_id, cfg, _logger: run_task_manifest(task_path, cfg, run_id),
            config=config,
            input_path=task_path,
            backend="task-manifest",
        )
        emit_result(result)

    @app.command("explain-task")
    def explain_task_cmd(
        task: Path,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        task_path = normalize_path(task)
        result = run_operation(
            "explain-task",
            lambda _run_id, _cfg, _logger: explain_task_manifest(task_path),
            config=config,
            input_path=task_path,
            backend="task-manifest",
        )
        emit_result(result)

    @app.command("validate-patch")
    def validate_patch_cmd(
        path: Path,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(path)
        result = run_operation(
            "validate-patch",
            lambda _run_id, _cfg, _logger: validate_patch(input_path),
            config=config,
            input_path=input_path,
            backend="jsonschema",
        )
        emit_result(result)

    @app.command("validate-task")
    def validate_task_cmd(
        path: Path,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(path)
        result = run_operation(
            "validate-task",
            lambda _run_id, _cfg, _logger: validate_task(input_path),
            config=config,
            input_path=input_path,
            backend="jsonschema",
        )
        emit_result(result)

    @app.command("validate-result")
    def validate_result_cmd(
        path: Path,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(path)
        result = run_operation(
            "validate-result",
            lambda _run_id, _cfg, _logger: validate_result(input_path),
            config=config,
            input_path=input_path,
            backend="jsonschema",
        )
        emit_result(result)
