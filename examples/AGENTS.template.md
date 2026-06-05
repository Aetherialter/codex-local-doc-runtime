# AGENTS.md Template

Use this template in projects where Codex should route local document work
through `codex-local-doc-runtime`.

```markdown
# Local Document Runtime

When working with local `.docx`, `.pdf`, or `.xlsx` files on Windows, use:

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv run docrt doctor --agent --office-smoke
```

If the runtime path is missing after migrating to a new machine:

```powershell
Set-Location D:\project\python
git clone https://github.com/Aetherialter/codex-local-doc-runtime.git
Set-Location D:\project\python\codex-local-doc-runtime
uv sync --dev
uv run docrt doctor --agent --office-smoke
```

Use `docrt` for inspection, rendering, conversion, patching, and verification:

```powershell
uv run docrt inspect-docx <path> [--output <json>]
uv run docrt read-docx <path> [--output <json>]
uv run docrt inspect-pdf <path> [--output <json>]
uv run docrt read-pdf <path> [--output <json>]
uv run docrt search-pdf <path> <query>
uv run docrt render-pdf <input> [output-dir]
uv run docrt inspect-xlsx <path> [--output <json>]
uv run docrt read-xlsx <path> [--output <json>]
uv run docrt validate-patch <patch.json>
uv run docrt patch-docx <input> <patch.json> <output> --dry-run
uv run docrt patch-docx <input> <patch.json> <output>
uv run docrt verify-docx <before> <after> [--expect <patch.json>]
uv run docrt patch-xlsx <input> <patch.json> <output> --dry-run
uv run docrt patch-xlsx <input> <patch.json> <output>
uv run docrt verify-xlsx <before> <after> [--expect <patch.json>]
uv run docrt docx-to-pdf <input> [output]
uv run docrt xlsx-to-pdf <input> [output]
uv run docrt validate-task <task.json>
uv run docrt explain-task <task.json>
uv run docrt run-task <task.json>
uv run docrt fingerprint <path>
uv run docrt batch-fingerprint <path> [<path> ...]
uv run docrt storage-report
uv run docrt clean --logs --work --cache
```

Rules:

- Run `uv run docrt doctor --agent --office-smoke` before processing documents
  when the environment is unknown.
- Inspect `error_code`, `error_message`, `log_path`, and
  `diagnostic_report_path` before changing code or retrying.
- Keep generated files under `outputs/`, `logs/`, or `work/`.
- Do not assume OCR, `.doc`, `.xls`, encrypted Office files, interactive Office
  dialogs, or complex PDF original-content editing are supported by `docrt`.
- Office COM conversion requires Microsoft Word or Microsoft Excel on the local
  machine.
- Rust acceleration is optional; without a local Rust/maturin build, `docrt`
  falls back to Python.
```
