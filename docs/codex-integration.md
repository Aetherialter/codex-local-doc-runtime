# Codex Integration

This document gives Codex and other coding agents a stable local document
runtime path for Windows DOCX, PDF, and XLSX work.

## Required Local Runtime

Use this repository as the document runtime:

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv run docrt doctor --agent --office-smoke
```

Run `doctor --agent` before document processing when the environment may have
changed. The JSON result reports Python package availability, writable runtime
paths, Microsoft Word COM, Microsoft Excel COM, Poppler tools, output paths,
Rust/Python core backend, and Windows path-length risk.

Generate a reusable Codex instruction fragment with:

```powershell
uv run docrt agent-config
```

## Agent Routing Rule

When a task involves local `.docx`, `.pdf`, or `.xlsx` files on Windows, prefer
`docrt` over ad hoc scripts.

Use these commands for analysis, conversion, patching, verification, and storage
management:

```powershell
uv run docrt inspect-docx <path>
uv run docrt read-docx <path>
uv run docrt inspect-pdf <path>
uv run docrt read-pdf <path>
uv run docrt search-pdf <path> <query>
uv run docrt render-pdf <input> [output-dir]
uv run docrt inspect-xlsx <path>
uv run docrt read-xlsx <path>
uv run docrt validate-patch <patch.json>
uv run docrt patch-docx <input> <patch.json> <output> --dry-run
uv run docrt patch-docx <input> <patch.json> <output>
uv run docrt verify-docx <before> <after> [--expect <patch.json>]
uv run docrt patch-xlsx <input> <patch.json> <output> --dry-run
uv run docrt patch-xlsx <input> <patch.json> <output>
uv run docrt verify-xlsx <before> <after> [--expect <patch.json>]
uv run docrt validate-task <task.json>
uv run docrt explain-task <task.json>
uv run docrt run-task <task.json>
uv run docrt fingerprint <path>
uv run docrt batch-fingerprint <path> [<path> ...]
uv run docrt batch-inspect <path> [<path> ...]
uv run docrt docx-to-pdf <input> [output]
uv run docrt xlsx-to-pdf <input> [output]
uv run docrt storage-report
uv run docrt clean --logs --work --cache
uv run docrt repair-plan --days 30
```

Use explicit output paths when repeatability matters:

```powershell
uv run docrt inspect-docx <path> --output outputs\agent\document.docx.inspect.json
uv run docrt inspect-pdf <path> --output outputs\agent\document.pdf.inspect.json
uv run docrt inspect-xlsx <path> --output outputs\agent\document.xlsx.inspect.json
```

## Failure Handling

Every command emits one JSON result. On failure, inspect these fields before
guessing a fix:

- `error_code`
- `error_message`
- `exception_type`
- `recovery_actions`
- `diagnostic_report_path`
- `log_path`

If `diagnostic_report_path` or `log_path` is present, read those files before
changing code or rerunning with different options.

## Capability Boundary

Supported:

- DOCX inspection
- DOCX to PDF export through Microsoft Word COM
- PDF inspection
- PDF rendering to PNG
- PDF text search
- XLSX inspection
- DOCX/XLSX explicit JSON patching
- DOCX/XLSX verification and comparison
- PDF additive annotations
- patch/task/result schema validation
- document fingerprinting, cache-read, batch-read, indexing, and search
- dry-run-first storage cleanup
- XLSX to PDF export through Microsoft Excel COM

Not supported:

- OCR
- `.doc`
- `.xls`
- encrypted Office files
- interactive Office dialog workflows
- complex PDF original-content editing

Office COM conversion requires Microsoft Word or Microsoft Excel to be
installed in the current Windows user session. Rust acceleration is optional:
without a local Rust/maturin build, `docrt` falls back to the Python core.

For edit workflows, first `read-*`, then `validate-patch`, then `patch-*`
with `--dry-run`, then execute the patch, then `verify-*`.

## Reusable Codex Instruction

Copy this into a project `AGENTS.md` when you want Codex to prefer `docrt`:

```text
When working with local .docx, .pdf, or .xlsx files on Windows, use the
codex-local-doc-runtime repository at D:\project\python\codex-local-doc-runtime.

Before processing documents, run:

Set-Location D:\project\python\codex-local-doc-runtime
uv run docrt doctor --agent --office-smoke

Use docrt for document inspection, rendering, patching, verification, and
conversion:

uv run docrt inspect-docx <path> [--output <json>]
uv run docrt read-docx <path> [--output <json>]
uv run docrt validate-patch <patch.json>
uv run docrt patch-docx <input> <patch.json> <output> --dry-run
uv run docrt patch-docx <input> <patch.json> <output>
uv run docrt verify-docx <before> <after> [--expect <patch.json>]
uv run docrt inspect-pdf <path> [--output <json>]
uv run docrt read-pdf <path> [--output <json>]
uv run docrt search-pdf <path> <query>
uv run docrt render-pdf <input> [output-dir]
uv run docrt inspect-xlsx <path> [--output <json>]
uv run docrt read-xlsx <path> [--output <json>]
uv run docrt patch-xlsx <input> <patch.json> <output> --dry-run
uv run docrt patch-xlsx <input> <patch.json> <output>
uv run docrt verify-xlsx <before> <after> [--expect <patch.json>]
uv run docrt docx-to-pdf <input> [output]
uv run docrt xlsx-to-pdf <input> [output]
uv run docrt validate-task <task.json>
uv run docrt explain-task <task.json>
uv run docrt run-task <task.json>

On failure, read log_path and diagnostic_report_path from the JSON result before
attempting a fix.

Do not assume OCR, .doc, .xls, encrypted Office files, interactive Office
dialogs, or complex PDF original-content editing are supported by docrt.
```
