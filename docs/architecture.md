# Architecture

`codex-local-doc-runtime` is a Windows local document runtime toolchain for
Agent workflows. The `main` branch intentionally standardizes one operational
path: `uv run docrt ...` on a machine with local Microsoft Word and Excel COM.

It is not a single-file end-user exe and it is not a cross-platform headless SDK.

## Goals

- Force a reproducible `uv`-managed source checkout entrypoint.
- Bootstrap `uv` with `winget` when it is missing and bootstrap is possible.
- Require local Microsoft Word and Microsoft Excel COM before document
  operations.
- Return structured errors when Office is missing; no no-Office fallback is
  implemented in main yet.
- Keep Rust acceleration optional below the Python orchestration layer.

## Runtime Shape

```text
PowerShell / Agent
  -> uv run docrt ...
     -> uv preflight / bootstrap
     -> Word + Excel COM preflight
     -> Python API / CLI
        -> direct DOCX / PDF / XLSX operation modules
        -> Office COM conversion worker for DOCX/XLSX PDF export
        -> Rust services           optional acceleration through docrt.core_bridge
```

## Main Components

- `docrt.runtime_env`: uv and local Office runtime preflight.
- `docrt.api`: public Python API facade. Document operations enter runtime
  preflight before direct suffix-based dispatch.
- `docrt.docx_ops`, `docrt.read_ops`, `docrt.patch_ops`, `docrt.verify_ops`:
  DOCX/XLSX/PDF read, inspect, patch, verify, compare, search, render, and
  annotation implementation after the required runtime is available.
- `docrt.office_convert`: Office COM implementation for DOCX/XLSX PDF export.
- `docrt.cli`: Typer command definitions.
- `docrt.task_ops`: repeatable task manifest execution through the same API
  facade.
- `docrt.runner`: operation lifecycle, result creation, logging, and diagnostics.
- `docrt.core_bridge`: optional Rust extension bridge with Python fallback.
- `docrt.agent`: Agent-facing configuration fragments and command groups.

## Runtime Preflight

All public document operations for `.docx`, `.pdf`, and `.xlsx` require:

- `uv` visible on PATH, or successful automatic bootstrap through `winget`.
- Microsoft Word COM.
- Microsoft Excel COM.

If Word or Excel is unavailable, document operations fail fast with structured
errors such as `OFFICE_COM_REQUIRED`, `WORD_COM_UNAVAILABLE`, or
`EXCEL_COM_UNAVAILABLE`.

## Rust Boundary

Rust does not own document workflow orchestration. It is a service layer used by
Python when available:

- file fingerprinting
- batch fingerprinting
- path containment checks
- JSON manifest preflight
- batch planning
- indexed text search

`docrt.core_bridge` imports `docrt_core` when the PyO3 extension is installed
and falls back to Python implementations when it is not. Public behavior must
remain available without Rust.

## Unsupported Boundaries

Unsupported boundaries remain explicit: legacy `.doc` / `.xls`, encrypted files,
OCR, interactive Office dialogs, and complex PDF original-content editing are
reported as unsupported rather than hidden behind ad hoc conversions.
