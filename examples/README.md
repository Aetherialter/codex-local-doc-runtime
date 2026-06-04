# Examples

This directory is reserved for small, non-sensitive example workflows.

The runtime output directories are ignored by Git, so generated files should be
created under `outputs/` or `work/` during local testing.

## Smoke Test Workflow

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv sync --dev
uv run docrt doctor
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
