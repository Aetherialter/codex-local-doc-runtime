from __future__ import annotations

from typing import Annotated

import typer

from docrt.agent import agent_config
from docrt.cli_support import ForceKillOpt, PopplerOpt, TimeoutOpt, emit_result, load_cli_config
from docrt.doctor import doctor_report
from docrt.runner import run_operation
from docrt.runtime_env import ensure_uv_available
from docrt.version_info import version_report


def register(app: typer.Typer) -> None:
    @app.command()
    def version(
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        result = run_operation(
            "version",
            lambda _run_id, _cfg, _logger: version_report(),
            config=config,
            backend="version",
        )
        emit_result(result)

    @app.command()
    def doctor(
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
        office_smoke: Annotated[bool, typer.Option("--office-smoke")] = False,
        agent: Annotated[bool, typer.Option("--agent")] = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        result = run_operation(
            "doctor",
            lambda _run_id, cfg, _logger: doctor_report(
                cfg, office_smoke=office_smoke, agent=agent
            ),
            config=config,
            backend="doctor",
        )
        emit_result(result)

    @app.command("bootstrap-uv")
    def bootstrap_uv_cmd(
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        result = run_operation(
            "bootstrap-uv",
            lambda _run_id, _cfg, _logger: ensure_uv_available(auto_install=True),
            config=config,
            backend="winget",
        )
        emit_result(result)

    @app.command("agent-config")
    def agent_config_cmd(
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        result = run_operation(
            "agent-config",
            lambda _run_id, cfg, _logger: agent_config(cfg),
            config=config,
            backend="agent",
        )
        emit_result(result)
