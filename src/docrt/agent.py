from __future__ import annotations

from pathlib import Path

from docrt.config import Config

DEFAULT_RUNTIME_PATH = Path(r"D:\project\python\codex-local-doc-runtime")
GITHUB_REPOSITORY = "https://github.com/Aetherialter/codex-local-doc-runtime.git"


def agent_config(config: Config) -> dict[str, object]:
    commands = _commands()
    return {
        "runtime": {
            "name": "codex-local-doc-runtime",
            "package": "docrt",
            "default_path": str(DEFAULT_RUNTIME_PATH),
            "repository": GITHUB_REPOSITORY,
            "run_from_project_root": True,
        },
        "environment": {
            "required": ["Windows 10/11", "PowerShell", "Git", "uv"],
            "optional": [
                "Microsoft Word for DOCX to PDF and DOCX COM smoke checks",
                "Microsoft Excel for XLSX to PDF and XLSX COM smoke checks",
                "Poppler for additional PDF rendering diagnostics",
                "Rust toolchain for optional docrt-core acceleration",
            ],
        },
        "paths": {
            "outputs": str(config.outputs_path),
            "logs": str(config.logs_path),
            "work": str(config.work_path),
            "diagnostics": str(config.diagnostics_path),
            "cache": str(config.work_path / "cache"),
        },
        "commands": commands,
        "unsupported": [
            "OCR",
            ".doc",
            ".xls",
            "encrypted Office files",
            "interactive Office dialog workflows",
            "complex PDF original-content editing",
        ],
        "agents_md": _agents_md_fragment(commands),
    }


def _commands() -> dict[str, list[str] | str]:
    return {
        "bootstrap": [
            r"Set-Location D:\project\python",
            f"git clone {GITHUB_REPOSITORY}",
            r"Set-Location D:\project\python\codex-local-doc-runtime",
            "uv sync --dev",
            "uv run docrt doctor --agent --office-smoke",
        ],
        "doctor": "uv run docrt doctor --agent --office-smoke",
        "read": [
            "uv run docrt fingerprint <path>",
            "uv run docrt batch-fingerprint <paths...>",
            "uv run docrt inspect-docx <path>",
            "uv run docrt read-docx <path>",
            "uv run docrt inspect-pdf <path>",
            "uv run docrt read-pdf <path>",
            "uv run docrt search-pdf <path> <query>",
            "uv run docrt inspect-xlsx <path>",
            "uv run docrt read-xlsx <path>",
        ],
        "convert": [
            "uv run docrt docx-to-pdf <input> [output]",
            "uv run docrt render-pdf <input> [output-dir]",
            "uv run docrt xlsx-to-pdf <input> [output]",
        ],
        "safe_edit": [
            "uv run docrt validate-patch <patch.json>",
            "uv run docrt patch-docx <input.docx> <patch.json> <output.docx> --dry-run",
            "uv run docrt patch-docx <input.docx> <patch.json> <output.docx>",
            "uv run docrt verify-docx <before.docx> <after.docx> --expect <patch.json>",
            "uv run docrt compare-docx <before.docx> <after.docx>",
            "uv run docrt patch-xlsx <input.xlsx> <patch.json> <output.xlsx> --dry-run",
            "uv run docrt patch-xlsx <input.xlsx> <patch.json> <output.xlsx>",
            "uv run docrt verify-xlsx <before.xlsx> <after.xlsx> --expect <patch.json>",
            "uv run docrt compare-xlsx <before.xlsx> <after.xlsx>",
        ],
        "task": [
            "uv run docrt validate-task <task.json>",
            "uv run docrt explain-task <task.json>",
            "uv run docrt run-task <task.json>",
            "uv run docrt validate-result <result.json>",
        ],
        "storage": [
            "uv run docrt storage-report",
            "uv run docrt clean --logs --work --cache",
            "uv run docrt clean --logs --work --cache --older-than 14 --yes",
        ],
        "maintenance": [
            "uv run docrt analyze-logs --days 30",
            "uv run docrt repair-plan --days 30",
            "uv run docrt maintenance",
            "uv run docrt job-start repair-plan --days 30",
        ],
    }


def _agents_md_fragment(commands: dict[str, list[str] | str]) -> str:
    safe_edit = "\n".join(str(command) for command in commands["safe_edit"])
    storage = "\n".join(str(command) for command in commands["storage"])
    maintenance = "\n".join(str(command) for command in commands["maintenance"])
    task = "\n".join(str(command) for command in commands["task"])
    return f"""# AGENTS.md Local Document Runtime Fragment

When working with local `.docx`, `.pdf`, or `.xlsx` files on Windows, prefer
`docrt` from `codex-local-doc-runtime` over ad hoc scripts.

Default runtime path:

```powershell
Set-Location {DEFAULT_RUNTIME_PATH}
uv run docrt doctor --agent --office-smoke
```

If the runtime path does not exist, restore it with:

```powershell
Set-Location D:\\project\\python
git clone {GITHUB_REPOSITORY}
Set-Location {DEFAULT_RUNTIME_PATH}
uv sync --dev
uv run docrt doctor --agent --office-smoke
```

Use the safe edit chain for DOCX/XLSX:

```powershell
{safe_edit}
```

Use task manifests for repeatable agent workflows:

```powershell
{task}
```

Manage local runtime artifacts with:

```powershell
{storage}
```

Before a development pass, review recent runtime feedback with:

```powershell
{maintenance}
```

Do not assume OCR, `.doc`, `.xls`, encrypted Office files, interactive Office
dialogs, or complex PDF original-content editing are supported. Office COM
conversion requires Microsoft Word or Microsoft Excel on the local machine.
Rust acceleration is optional and falls back to Python when the native extension
is unavailable.
"""
