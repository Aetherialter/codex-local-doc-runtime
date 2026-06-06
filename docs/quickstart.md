# Quickstart

Use these five commands after cloning the repository on Windows. They verify the
mainline `uv` + local Microsoft Office runtime without exposing internal command
chains to end users.

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv sync --dev
uv run docrt version
uv run docrt doctor --agent --office-smoke
uv run docrt agent-config
```

Expected result:

- `version` reports `1.1.0`.
- `doctor --agent --office-smoke` reports `agent.ready=true`.
- `word_com_available=true` and `excel_com_available=true`.
- Rust may report either `backend=rust` or `backend=python`; Rust is optional.

If `uv` is missing, bootstrap it first:

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
.\scripts\bootstrap-uv.ps1
```

If Office is missing, install desktop Microsoft Word and Excel, close any
first-run prompts, then rerun:

```powershell
uv run docrt doctor --agent --office-smoke
```

`main` does not provide a no-Office fallback in v1.1. Single-file exe, GUI/TUI,
PyInstaller, and Nuitka packaging belong to a separate distribution branch.
