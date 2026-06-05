# Codex Integration

This document gives Codex and other coding agents a stable local document
runtime path for Windows DOCX, PDF, and XLSX work.

## Required Local Runtime

Use this repository as the document runtime:

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv run docrt doctor
```

Run `doctor` before document processing when the environment may have changed.
The JSON result reports Python package availability, Microsoft Word COM,
Microsoft Excel COM, Poppler tools, output paths, and Windows path-length risk.

## Agent Routing Rule

When a task involves local `.docx`, `.pdf`, or `.xlsx` files on Windows, prefer
`docrt` over ad hoc scripts.

Use these commands for analysis and conversion:

```powershell
uv run docrt inspect-docx <path>
uv run docrt inspect-pdf <path>
uv run docrt render-pdf <input> [output-dir]
uv run docrt inspect-xlsx <path>
uv run docrt docx-to-pdf <input> [output]
uv run docrt xlsx-to-pdf <input> [output]
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
- XLSX inspection
- XLSX to PDF export through Microsoft Excel COM

Not supported:

- OCR
- `.doc`
- `.xls`
- encrypted Office files
- interactive Office dialog workflows
- complex PDF original-content editing
- direct DOCX/XLSX patch editing in the current release

For edit workflows, use `docrt` as the inspection, conversion, logging, and
diagnostics layer. Apply edits only through explicit future `docrt` edit
commands or another reviewed document editing tool.

## Reusable Codex Instruction

Copy this into a project `AGENTS.md` when you want Codex to prefer `docrt`:

```text
When working with local .docx, .pdf, or .xlsx files on Windows, use the
codex-local-doc-runtime repository at D:\project\python\codex-local-doc-runtime.

Before processing documents, run:

Set-Location D:\project\python\codex-local-doc-runtime
uv run docrt doctor

Use docrt for document inspection, rendering, and conversion:

uv run docrt inspect-docx <path> [--output <json>]
uv run docrt inspect-pdf <path> [--output <json>]
uv run docrt render-pdf <input> [output-dir]
uv run docrt inspect-xlsx <path> [--output <json>]
uv run docrt docx-to-pdf <input> [output]
uv run docrt xlsx-to-pdf <input> [output]

On failure, read log_path and diagnostic_report_path from the JSON result before
attempting a fix.

Do not assume OCR, .doc, .xls, encrypted Office files, interactive Office
dialogs, complex PDF original-content editing, or direct DOCX/XLSX patch editing
are supported by docrt.
```
