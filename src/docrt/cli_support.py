from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Any

import typer

from docrt.config import Config
from docrt.jsonutil import dumps
from docrt.models import exit_code_for_result

PopplerOpt = Annotated[str | None, typer.Option("--poppler-path")]
TimeoutOpt = Annotated[int | None, typer.Option("--timeout", min=1)]
ForceKillOpt = Annotated[bool, typer.Option("--force-kill-office")]
OutputOpt = Annotated[Path | None, typer.Option("--output", "-o")]
DryRunOpt = Annotated[bool, typer.Option("--dry-run")]
ExpectOpt = Annotated[Path | None, typer.Option("--expect")]


def load_cli_config(
    poppler_path: str | None,
    timeout: int | None,
    force_kill_office: bool,
) -> Config:
    return Config.load(
        poppler_path=poppler_path,
        timeout=timeout,
        force_kill_office=force_kill_office,
    )


def emit_result(result: Any) -> None:
    text = dumps(result.to_dict(), pretty=True) + "\n"
    sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    raise typer.Exit(int(exit_code_for_result(result)))
