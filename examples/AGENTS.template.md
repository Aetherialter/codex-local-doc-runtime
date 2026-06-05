# AGENTS.md Template

Use this template in projects where Codex should route local document work
through `codex-local-doc-runtime`.

```markdown
# Local Document Runtime

When working with local `.docx`, `.pdf`, or `.xlsx` files on Windows, use:

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv run docrt doctor
```

Use `docrt` for inspection, rendering, and conversion:

```powershell
uv run docrt inspect-docx <path> [--output <json>]
uv run docrt inspect-pdf <path> [--output <json>]
uv run docrt render-pdf <input> [output-dir]
uv run docrt inspect-xlsx <path> [--output <json>]
uv run docrt docx-to-pdf <input> [output]
uv run docrt xlsx-to-pdf <input> [output]
```

Rules:

- Run `uv run docrt doctor` before processing documents when the environment is
  unknown.
- Inspect `error_code`, `error_message`, `log_path`, and
  `diagnostic_report_path` before changing code or retrying.
- Keep generated files under `outputs/`, `logs/`, or `work/`.
- Do not assume OCR, `.doc`, `.xls`, encrypted Office files, interactive Office
  dialogs, complex PDF original-content editing, or direct DOCX/XLSX patch
  editing are supported by `docrt`.
```
