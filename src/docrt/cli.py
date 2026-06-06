from __future__ import annotations

import typer

from docrt import cli_batch, cli_config, cli_document, cli_maintenance, cli_runtime, cli_task

app = typer.Typer(no_args_is_help=True, add_completion=False)

cli_runtime.register(app)
cli_document.register(app)
cli_task.register(app)
cli_batch.register(app)
cli_maintenance.register(app)
cli_config.register(app)
