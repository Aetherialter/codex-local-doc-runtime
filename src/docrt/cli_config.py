from __future__ import annotations

from typing import Annotated

import typer

from docrt.cli_support import emit_result
from docrt.config import Config
from docrt.config_cli import config_init, config_set, config_show
from docrt.runner import run_operation


def register(app: typer.Typer) -> None:
    config_app = typer.Typer(no_args_is_help=True, add_completion=False)
    app.add_typer(config_app, name="config")

    @config_app.command("init")
    def config_init_cmd(force: Annotated[bool, typer.Option("--force")] = False) -> None:
        config = Config.load()
        result = run_operation(
            "config-init",
            lambda _run_id, _cfg, _logger: config_init(force=force),
            config=config,
            backend="config",
        )
        emit_result(result)

    @config_app.command("show")
    def config_show_cmd() -> None:
        config = Config.load()
        result = run_operation(
            "config-show",
            lambda _run_id, cfg, _logger: config_show(cfg),
            config=config,
            backend="config",
        )
        emit_result(result)

    @config_app.command("set")
    def config_set_cmd(key: str, value: str) -> None:
        config = Config.load()
        result = run_operation(
            "config-set",
            lambda _run_id, _cfg, _logger: config_set(key, value),
            config=config,
            backend="config",
        )
        emit_result(result)
