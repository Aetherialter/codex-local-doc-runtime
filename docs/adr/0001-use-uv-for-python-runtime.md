# ADR-0001: Use uv for Python Runtime Management

## Background

The project should work after cloning on a new Windows machine without relying
on a globally configured `python` or `py` command.

## Decision

Use `uv` for dependency synchronization, Python version management, local command
execution, and lockfile-based reproducibility.

## Reasons

`uv` provides fast dependency installation, a project lockfile, and a consistent
`uv run` command for invoking the CLI and test tools.

## Advantages

- Reproducible setup through `uv.lock`.
- No dependency on a globally installed Python command.
- Consistent PowerShell-friendly commands for setup, testing, and CLI use.

## Disadvantages

- Users must install `uv` before first use.
- Some users may be less familiar with `uv` than `pip` or `venv`.

## Alternatives

- `pip` plus `venv`: familiar, but less reproducible and more dependent on the
  user's global Python installation.
- Poetry: mature project workflow, but heavier than needed for this small CLI
  runtime.

## Impact

The README and CI both use `uv` as the single supported development and
execution path.
