# Architecture

`codex-local-doc-runtime` provides a Windows-first command line runtime for
local document processing. It is designed for automation agents that need stable
machine-readable results instead of interactive desktop workflows.

## Goals

- Provide a single `docrt` CLI for DOCX, PDF, and XLSX tasks.
- Return a consistent JSON result shape from every command.
- Keep all generated logs, diagnostics, and output files in predictable local
  directories.
- Isolate Microsoft Office COM conversion work in subprocesses so the parent
  process can enforce timeouts and collect diagnostics.
- Use `uv` so a cloned repository can recreate its Python environment without
  relying on a global Python command.

## Main Components

- `docrt.cli`: Typer command definitions and option wiring.
- `docrt.runner`: operation lifecycle, result creation, logging, and diagnostics.
- `docrt.config`: configuration loading from CLI options, environment variables,
  `docrt.config.json`, and defaults.
- `docrt.docx_ops`: DOCX inspection through `python-docx`.
- `docrt.pdf_ops`: PDF inspection and rendering through PyMuPDF.
- `docrt.xlsx_ops`: XLSX inspection through `openpyxl` and `pandas`.
- `docrt.docx_patch`: DOCX patch operations and best-effort run-aware format
  preservation.
- `docrt.xlsx_patch`: XLSX patch operations.
- `docrt.patch_common`: shared patch loading, validation, summary, and helper
  functions.
- `docrt.patch_ops`: backward-compatible facade that exports `patch_docx` and
  `patch_xlsx`.
- `docrt.log_analysis`: reads persisted error JSONL logs and groups recurring
  failures by error code, operation, module, and exception type.
- `docrt.repair_plan`: converts log-analysis output into a ranked, persisted
  next-fix plan without auto-applying risky changes.
- `docrt.office_convert`: parent-side Office conversion orchestration.
- `docrt.office_worker`: subprocess entrypoint for Word and Excel COM work.
- `docrt.office_process`: Office process snapshots and cleanup diagnostics.
- `docrt.poppler`: Poppler tool discovery for auxiliary PDF diagnostics.
- `docrt.core_bridge`: Optional Rust acceleration for hashing, batch
  fingerprints, path checks, JSON preflight validation, and indexed search.
- `docrt.agent`: Agent-facing configuration fragments and bootstrap command
  groups.

## Runtime Flow

1. The user runs a `docrt` command.
2. CLI options are merged with environment variables, local config, and defaults.
3. `run_operation` creates a run ID, starts structured logging, and invokes the
   selected backend.
4. The backend returns structured data or raises an exception.
5. The runner emits the normalized JSON result, writes a JSONL log, and creates a
   diagnostic report on failure.

## Portability Model

The repository is intended to be cloned on a fresh Windows machine and prepared
with:

```powershell
uv sync --dev
uv run docrt doctor --agent --office-smoke
```

Microsoft Word, Microsoft Excel, and Poppler are external runtime capabilities.
The `doctor` command reports their availability so a missing desktop dependency
is visible before conversion work starts.

v1.0 keeps portability explicit rather than implicit:

- Office COM conversion is Windows desktop only.
- Non-Office DOCX/PDF/XLSX commands are best-effort outside Windows.
- Legacy `.doc` / `.xls`, encrypted files, OCR, interactive Office dialogs, and
  complex PDF original-content editing are reported as unsupported boundaries
  instead of being handled through ad hoc fallbacks.
