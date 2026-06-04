# Contributing

Thank you for considering a contribution to `codex-local-doc-runtime`.

This project is a Windows-first local document runtime. Changes should preserve
the non-interactive JSON CLI contract and avoid depending on a global Python
installation.

## Development Setup

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv sync --dev
uv run docrt doctor
```

## Quality Gates

Run these commands before opening a pull request:

```powershell
uv run ruff format .
uv run ruff check .
uv run pytest
uv run pytest --cov=docrt
```

If your change touches Office COM conversion behavior, also run the affected
DOCX or XLSX conversion command on a Windows machine with Microsoft Office
installed.

## Pull Request Guidelines

- Keep changes focused on one behavior or maintenance goal.
- Include tests for core logic, path handling, error handling, and JSON result
  shape changes.
- Update `README.md` when user-facing commands, dependencies, or setup steps
  change.
- Add an ADR under `docs/adr/` when introducing a major dependency, runtime
  strategy, or architectural boundary.
