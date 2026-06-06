from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from docrt.cache_ops import (
    batch_fingerprint,
    batch_inspect,
    batch_read,
    cache_read,
    fingerprint_file,
    index,
    search,
)
from docrt.cli_support import ForceKillOpt, PopplerOpt, TimeoutOpt, emit_result, load_cli_config
from docrt.paths import normalize_path
from docrt.runner import run_operation


def register(app: typer.Typer) -> None:
    @app.command("fingerprint")
    def fingerprint_cmd(
        path: Path,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(path)
        result = run_operation(
            "fingerprint",
            lambda _run_id, _cfg, _logger: fingerprint_file(input_path),
            config=config,
            input_path=input_path,
            backend="core-bridge",
        )
        emit_result(result)

    @app.command("batch-fingerprint")
    def batch_fingerprint_cmd(
        paths: list[Path],
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        result = run_operation(
            "batch-fingerprint",
            lambda _run_id, _cfg, _logger: batch_fingerprint(paths),
            config=config,
            backend="core-bridge",
        )
        emit_result(result)

    @app.command("cache-read")
    def cache_read_cmd(
        path: Path,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        input_path = normalize_path(path)
        result = run_operation(
            "cache-read",
            lambda _run_id, cfg, _logger: cache_read(input_path, cfg),
            config=config,
            input_path=input_path,
            backend="core-bridge",
        )
        emit_result(result)

    @app.command("batch-read")
    def batch_read_cmd(
        paths: list[Path],
        use_cache: Annotated[bool, typer.Option("--use-cache")] = False,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        result = run_operation(
            "batch-read",
            lambda _run_id, cfg, _logger: batch_read(paths, cfg, use_cache=use_cache),
            config=config,
            backend="core-bridge",
        )
        emit_result(result)

    @app.command("batch-inspect")
    def batch_inspect_cmd(
        paths: list[Path],
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        result = run_operation(
            "batch-inspect",
            lambda _run_id, _cfg, _logger: batch_inspect(paths),
            config=config,
            backend="inspect",
        )
        emit_result(result)

    @app.command("index")
    def index_cmd(
        paths: list[Path],
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        result = run_operation(
            "index",
            lambda _run_id, cfg, _logger: index(paths, cfg),
            config=config,
            backend="core-bridge",
        )
        emit_result(result)

    @app.command("search")
    def search_cmd(
        query: str,
        poppler_path: PopplerOpt = None,
        timeout: TimeoutOpt = None,
        force_kill_office: ForceKillOpt = False,
    ) -> None:
        config = load_cli_config(poppler_path, timeout, force_kill_office)
        result = run_operation(
            "search",
            lambda _run_id, cfg, _logger: search(query, cfg),
            config=config,
            backend="core-bridge",
        )
        emit_result(result)
