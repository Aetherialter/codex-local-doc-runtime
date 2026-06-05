# Smoke Test Workflow

Run these commands from the repository root on Windows.

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv sync --dev
uv run docrt doctor --agent --office-smoke
uv run docrt agent-config
```

Inspect the sample files:

```powershell
uv run docrt inspect-docx examples\fixtures\sample.docx --output outputs\smoke\sample.docx.inspect.json
uv run docrt inspect-pdf examples\fixtures\sample.pdf --output outputs\smoke\sample.pdf.inspect.json
uv run docrt search-pdf examples\fixtures\sample.pdf sample --output outputs\smoke\sample.pdf.search.json
uv run docrt inspect-xlsx examples\fixtures\sample.xlsx --output outputs\smoke\sample.xlsx.inspect.json
```

Render and convert:

```powershell
uv run docrt render-pdf examples\fixtures\sample.pdf outputs\smoke\sample-pdf-pages
uv run docrt docx-to-pdf examples\fixtures\sample.docx outputs\smoke\sample-docx.pdf
uv run docrt xlsx-to-pdf examples\fixtures\sample.xlsx outputs\smoke\sample-xlsx.pdf
```

Expected local outputs:

```text
outputs/smoke/sample.docx.inspect.json
outputs/smoke/sample.pdf.inspect.json
outputs/smoke/sample.pdf.search.json
outputs/smoke/sample.xlsx.inspect.json
outputs/smoke/sample-pdf-pages/page-0001.png
outputs/smoke/sample-docx.pdf
outputs/smoke/sample-xlsx.pdf
```

`outputs/`, `logs/`, and `work/` are ignored by Git.
