# codex-local-doc-runtime

`docrt` is a Windows-first local document runtime for Codex and other automation
tools. It provides a stable non-interactive JSON CLI and Python package for
DOCX, PDF, and XLSX processing.

The project is designed so a fresh Windows machine with the required system
tools can clone the repository, sync dependencies with `uv`, run diagnostics,
and start using the `docrt` CLI without relying on a global Python command.

## Features

- Inspect `.docx` files with `python-docx`.
- Convert `.docx` to PDF through Microsoft Word COM.
- Inspect and render `.pdf` files with PyMuPDF.
- Inspect `.xlsx` files with `openpyxl` and `pandas`.
- Convert `.xlsx` to PDF through Microsoft Excel COM.
- Emit one normalized JSON result from every CLI operation.
- Write structured JSONL logs and failure diagnostics for every run.
- Diagnose Python packages, Office COM, Poppler, and runtime paths with
  `docrt doctor`.
- Generate Codex/Agent integration instructions with `docrt agent-config`.
- Check Agent readiness with `docrt doctor --agent`.
- Use an optional Rust core for hashing, file fingerprints, path checks, and
  JSON preflight validation.
- Validate patch, task, and result JSON through committed schemas.
- Run replayable single-step or multi-step Agent task manifests.
- Report storage usage and clean generated logs, outputs, work files, caches,
  and build artifacts through explicit dry-run-first commands.

## Capability Boundary

Current CLI capabilities:

- analyze DOCX structure and text with `inspect-docx`
- analyze PDF metadata, page geometry, and text layer status with `inspect-pdf`
- render PDF pages to PNG with `render-pdf`
- analyze XLSX workbook sheets and preview cell data with `inspect-xlsx`
- export DOCX to PDF with `docx-to-pdf`
- export XLSX to PDF with `xlsx-to-pdf`
- read DOCX/PDF/XLSX into a unified `content_blocks` JSON protocol
- patch DOCX/XLSX through explicit JSON patch files with dry-run and expected
  value conflict checks
- verify and compare DOCX/XLSX changes with structured diffs
- annotate PDFs with safe additive annotations
- validate JSON schemas for patches, tasks, and command results
- fingerprint, cache-read, batch-read, index, and search local documents
- execute single-step or multi-step document operations from task manifests
- explain task manifests before execution with `explain-task`
- inspect and clean local runtime artifacts without deleting outside the
  project root

Current CLI edits DOCX and XLSX only through explicit patch JSON files and never
overwrites the input document by default. PDF original-content editing is not
supported; only additive annotations are supported.

## Supported Scope

Supported:

- `.docx`
- `.pdf`
- `.xlsx`

Not supported:

- OCR
- `.doc`
- `.xls`
- encrypted Office files
- Office flows that require interactive dialogs

## Requirements

Required for all commands:

- Windows
- PowerShell
- Git, or a ZIP download of this repository from GitHub
- Internet access for first-time dependency installation
- `uv`
- Python 3.12+, installed and managed through `uv`

Required for Office PDF export:

- Microsoft Word for `docx-to-pdf`
- Microsoft Excel for `xlsx-to-pdf`

Required or recommended for PDF diagnostics/rendering workflows:

- Poppler tools: `pdfinfo`, `pdftoppm`, `pdftocairo`

Optional for native acceleration:

- Rust toolchain through rustup/cargo
- `maturin`, installed through this project's `uv sync --dev`

Install Git and `uv` before using this project:

```powershell
winget install --id Git.Git -e
winget install --id astral-sh.uv -e
```

Restart PowerShell after installation if `git` or `uv` is not immediately
available.

## Quick Start After Clone

Use this path on a fresh Windows machine after installing the required system
tools listed above.

```powershell
Set-Location D:\project\python
git clone https://github.com/Aetherialter/codex-local-doc-runtime.git
Set-Location D:\project\python\codex-local-doc-runtime
uv sync --dev
uv run docrt doctor --agent --office-smoke
uv run pytest
```

To enable the optional Rust core on a development machine:

```powershell
winget install --id Rustlang.Rustup -e
Set-Location D:\project\python\codex-local-doc-runtime
uv sync --dev
uv run maturin develop --manifest-path crates\docrt-core\Cargo.toml
uv run docrt doctor --agent --office-smoke
```

If the Rust extension is not built, `docrt` falls back to the Python core for
hashing, path safety checks, and JSON preflight validation.

## Using With Codex

For durable Codex behavior across conversations, read
`docs/codex-integration.md` and copy `examples/AGENTS.template.md` into your
target project as `AGENTS.md`.

You can also generate a machine-readable configuration and Markdown fragment:

```powershell
uv run docrt agent-config
```

Minimal instruction:

```text
When working with local .docx, .pdf, or .xlsx files on Windows, use the
codex-local-doc-runtime repository at D:\project\python\codex-local-doc-runtime.
Before processing documents, run:

Set-Location D:\project\python\codex-local-doc-runtime
uv run docrt doctor --agent --office-smoke

Use these commands for document inspection and conversion:

uv run docrt inspect-docx <path> [--output <json>]
uv run docrt read-docx <path> [--output <json>]
uv run docrt validate-patch <patch.json>
uv run docrt patch-docx <input> <patch.json> <output> [--dry-run]
uv run docrt verify-docx <before> <after> [--expect <patch.json>]
uv run docrt compare-docx <before> <after>
uv run docrt docx-to-pdf <input> [output]
uv run docrt inspect-pdf <path> [--output <json>]
uv run docrt read-pdf <path> [--output <json>]
uv run docrt render-pdf <input> [output-dir]
uv run docrt annotate-pdf <input> <annotations.json> <output>
uv run docrt inspect-xlsx <path> [--output <json>]
uv run docrt read-xlsx <path> [--output <json>]
uv run docrt patch-xlsx <input> <patch.json> <output> [--dry-run]
uv run docrt verify-xlsx <before> <after> [--expect <patch.json>]
uv run docrt compare-xlsx <before> <after>
uv run docrt xlsx-to-pdf <input> [output]
uv run docrt validate-task <task.json>
uv run docrt explain-task <task.json>
uv run docrt run-task <task.json>

Do not assume OCR, .doc, .xls, encrypted Office files, or direct PDF editing are
supported by docrt.
```

## CLI Commands

All commands print JSON to stdout, write a JSONL log, and return a fixed exit
code.

```powershell
uv run docrt doctor
uv run docrt doctor --agent --office-smoke
uv run docrt agent-config
uv run docrt inspect-docx path\to\file.docx
uv run docrt inspect-docx path\to\file.docx --output outputs\file.docx.inspect.json
uv run docrt read-docx path\to\file.docx --output outputs\file.docx.read.json
uv run docrt patch-docx path\to\file.docx path\to\patch.json outputs\file.patched.docx
uv run docrt patch-docx path\to\file.docx path\to\patch.json outputs\file.patched.docx --dry-run
uv run docrt verify-docx path\to\file.docx outputs\file.patched.docx
uv run docrt compare-docx path\to\file.docx outputs\file.patched.docx
uv run docrt docx-to-pdf path\to\file.docx
uv run docrt inspect-pdf path\to\file.pdf
uv run docrt inspect-pdf path\to\file.pdf --output outputs\file.pdf.inspect.json
uv run docrt read-pdf path\to\file.pdf --output outputs\file.pdf.read.json
uv run docrt render-pdf path\to\file.pdf
uv run docrt annotate-pdf path\to\file.pdf path\to\annotations.json outputs\file.annotated.pdf
uv run docrt inspect-xlsx path\to\file.xlsx
uv run docrt inspect-xlsx path\to\file.xlsx --output outputs\file.xlsx.inspect.json
uv run docrt read-xlsx path\to\file.xlsx --output outputs\file.xlsx.read.json
uv run docrt patch-xlsx path\to\file.xlsx path\to\patch.json outputs\file.patched.xlsx
uv run docrt patch-xlsx path\to\file.xlsx path\to\patch.json outputs\file.patched.xlsx --dry-run
uv run docrt verify-xlsx path\to\file.xlsx outputs\file.patched.xlsx
uv run docrt compare-xlsx path\to\file.xlsx outputs\file.patched.xlsx
uv run docrt xlsx-to-pdf path\to\file.xlsx
uv run docrt validate-patch path\to\patch.json
uv run docrt validate-task path\to\task.json
uv run docrt explain-task path\to\task.json
uv run docrt fingerprint path\to\file.docx
uv run docrt cache-read path\to\file.docx
uv run docrt batch-read path\to\a.docx path\to\b.pdf --use-cache
uv run docrt batch-inspect path\to\a.docx path\to\b.xlsx --use-cache
uv run docrt index path\to\a.docx path\to\b.xlsx
uv run docrt search "keyword"
uv run docrt storage-report
uv run docrt clean --logs --work --cache
uv run docrt clean --logs --work --cache --yes
uv run docrt config show
uv run docrt run-task path\to\task.json
```

Common options:

```powershell
uv run docrt doctor --poppler-path D:\tools\poppler\bin
uv run docrt docx-to-pdf input.docx output.pdf --timeout 30
uv run docrt xlsx-to-pdf input.xlsx output.pdf --force-kill-office
```

`--force-kill-office` only enables force cleanup when the runtime config also
allows it. Default cleanup only targets Office processes that appear to have
been created by the current conversion task.

## Output Rules

Run ID:

```text
YYYYMMDD-HHMMSS-randomid
```

Default paths:

```text
outputs/
logs/
work/
outputs/diagnostics/
```

Generated files:

```text
logs/{run_id}.jsonl
outputs/diagnostics/{run_id}.diagnostic.json
outputs/{input-stem}.pdf
outputs/{input-stem}/page-{page:04d}.png
outputs/{input-name}.inspect.json
```

These directories are local runtime outputs and are ignored by Git.

`storage-report` includes file count, total bytes, and `oldest_file_time` for
each local runtime target. `clean` is dry-run by default and deletes only when
`--yes` is present.

## Result Shape

Every operation returns the same JSON shape:

```json
{
  "ok": true,
  "operation": "doctor",
  "input_path": null,
  "output_path": null,
  "backend": "doctor",
  "run_id": "20260604-120000-abcdef",
  "started_at": "2026-06-04T12:00:00.000Z",
  "ended_at": "2026-06-04T12:00:00.100Z",
  "duration_ms": 100,
  "error_code": null,
  "error_message": null,
  "exception_type": null,
  "traceback": null,
  "recovery_actions": [],
  "diagnostic_report_path": null,
  "log_path": "logs/run.jsonl",
  "data": {}
}
```

## Configuration

Configuration priority:

1. CLI options
2. environment variables
3. `docrt.config.json`
4. defaults

Supported environment variables:

- `POPPLER_PATH`
- `DOCRT_TIMEOUT_SECONDS`
- `DOCRT_ALLOW_FORCE_KILL_OFFICE`
- `DOCRT_OUTPUTS_DIR`
- `DOCRT_LOGS_DIR`
- `DOCRT_WORK_DIR`
- `DOCRT_DIAGNOSTICS_DIR`

Example:

```powershell
$env:POPPLER_PATH = "D:\tools\poppler\bin"
uv run docrt doctor
```

## Development

```powershell
uv sync --dev
uv run ruff format .
uv run ruff check .
uv run pytest
uv run pytest --cov=docrt
$env:PYO3_PYTHON = (Resolve-Path .venv\Scripts\python.exe).Path
cargo fmt --check --manifest-path crates\docrt-core\Cargo.toml
cargo clippy --manifest-path crates\docrt-core\Cargo.toml -- -D warnings
cargo test --manifest-path crates\docrt-core\Cargo.toml
uv run maturin develop --manifest-path crates\docrt-core\Cargo.toml
```

## Examples

The `examples/fixtures/` directory contains small non-sensitive sample files.
Run the full local smoke workflow from `examples/run-smoke.md`.

## CI

GitHub Actions runs on `windows-latest` and verifies:

- dependency sync through `uv`
- formatting with `ruff format --check`
- linting with `ruff check`
- unit tests with `pytest`
- coverage smoke test with `pytest --cov=docrt`
- Rust core checks with `cargo fmt`, `cargo clippy`, and `cargo test`

Office desktop applications are not assumed in CI. Use
`docrt doctor --agent --office-smoke` locally to validate Word COM and Excel COM
availability.

## Troubleshooting

If `uv` is not found, install it and restart PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

If Poppler is missing, install Poppler and pass its `bin` directory:

```powershell
uv run docrt doctor --poppler-path D:\tools\poppler\bin
```

If Word or Excel COM is unavailable, confirm that Microsoft Word or Excel is
installed and can open normally in the current Windows user session:

```powershell
uv run docrt doctor
```

If a command fails, inspect the JSON result fields:

- `error_code`
- `error_message`
- `exception_type`
- `recovery_actions`
- `diagnostic_report_path`
- `log_path`

If Windows reports path length risk, clone the repository into a shorter path,
for example:

```powershell
Set-Location D:\src
git clone https://github.com/Aetherialter/codex-local-doc-runtime.git
```

## Project Structure

```text
codex-local-doc-runtime/
  .github/workflows/ci.yml
  crates/docrt-core/
  docs/
    adr/
    architecture.md
  schemas/
  examples/
  src/docrt/
  tests/
  CHANGELOG.md
  CONTRIBUTING.md
  LICENSE
  README.md
  SECURITY.md
  pyproject.toml
  uv.lock
```

## Architecture Notes

Read `docs/architecture.md` for the runtime design and `docs/adr/` for the main
technical decisions.

Read `docs/codex-integration.md` for Agent routing rules and failure-handling
guidance.

Read `docs/patch-protocol.md` for DOCX/XLSX patch JSON operations.

Read `docs/task-manifest.md` for replayable Agent task manifests.

Read `docs/troubleshooting.md` for error-code recovery guidance.

Read `docs/pdf-annotation.md` for safe additive PDF annotation.

Read `docs/batch-and-cache-design.md` for fingerprint, cache, index, and search
workflows.

Read `docs/storage-management.md` for dry-run-first cleanup commands and
scheduled cleanup examples.

The most important boundaries are:

- CLI output is a JSON contract.
- Office COM conversion is isolated in subprocess workers.
- Runtime outputs stay under ignored local directories.
- `uv` is the supported environment and execution path.
