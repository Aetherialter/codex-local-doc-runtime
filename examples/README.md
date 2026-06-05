# Examples

This directory contains small, non-sensitive example workflows and fixtures.

The runtime output directories are ignored by Git, so generated files should be
created under `outputs/` or `work/` during local testing.

## Files

- `fixtures/sample.docx`: DOCX inspection and DOCX to PDF smoke fixture.
- `fixtures/sample.pdf`: PDF inspection and rendering smoke fixture.
- `fixtures/sample.xlsx`: XLSX inspection and XLSX to PDF smoke fixture.
- `run-smoke.md`: full local smoke workflow.

## Smoke Test Workflow

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv sync --dev
uv run docrt doctor --agent --office-smoke
uv run docrt agent-config
uv run docrt inspect-pdf .\path\to\sample.pdf
uv run docrt render-pdf .\path\to\sample.pdf
```

For DOCX and XLSX conversion examples, use local documents that do not contain
private data:

```powershell
uv run docrt inspect-docx .\path\to\sample.docx
uv run docrt docx-to-pdf .\path\to\sample.docx
uv run docrt inspect-xlsx .\path\to\sample.xlsx
uv run docrt xlsx-to-pdf .\path\to\sample.xlsx
```

Task manifests can be checked before execution:

```powershell
uv run docrt validate-task examples\tasks\xlsx-patch-verify.json
uv run docrt explain-task examples\tasks\xlsx-patch-verify.json
```
