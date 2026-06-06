# Release Notes: v1.1.0

`docrt` v1.1.0 redirects `main` into a fixed Windows local runtime toolchain:
`uv run docrt ...` plus local Microsoft Word and Excel COM. The release is meant
for Agent workflows and developer-controlled source checkouts, not standalone
end-user exe distribution.

## Added

- `docrt.runtime_env` preflight for required `uv`, Word COM, and Excel COM.
- `scripts\bootstrap-uv.ps1` and `docrt bootstrap-uv` for uv bootstrap checks.
- Public `docrt.api` facade for document inspect, read, render, search, patch,
  verify, compare, annotation, and PDF export operations.
- PDF annotation task support through `annotate-pdf`.
- Batch/cache/fingerprint/index/search commands backed by optional Rust
  acceleration through `docrt.core_bridge`.
- Agent-ready `doctor --agent --office-smoke` and `agent-config` output for
  repeatable local environment checks.
- Structured errors for `UV_UNAVAILABLE`, `UV_BOOTSTRAP_FAILED`,
  `OFFICE_COM_REQUIRED`, `WORD_COM_UNAVAILABLE`, `EXCEL_COM_UNAVAILABLE`, and
  `CORRUPT_DOCUMENT`.

## Changed

- `main` is no longer described as a cross-platform headless SDK or exe delivery
  line. It is a Windows `uv` + local Office runtime toolchain.
- `.docx`, `.pdf`, and `.xlsx` public document operations now require the
  mainline runtime preflight before dispatch.
- Missing desktop Word or Excel fails fast with structured diagnostics instead
  of silently falling back to another engine.
- CLI code was split into feature modules while preserving existing command
  names and arguments.
- Rust remains optional; when the PyO3 module is unavailable, Python fallback is
  used for acceleration primitives only.

## Breaking Boundaries

- Windows without desktop Microsoft Word and Excel is not a supported document
  processing target for v1.1.
- Linux, macOS, WSL, Docker, and GitHub-hosted Windows runners can validate many
  tests, but they do not prove real desktop Office success.
- OCR, legacy `.doc` / `.xls`, encrypted files, interactive Office dialogs, and
  complex PDF original-content editing remain unsupported.
- Single-file exe, GUI/TUI, PyInstaller, and Nuitka packaging are out of scope
  for `main`.

## Validation

Release candidates should pass:

```powershell
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
uv build
```

Rust optional layer:

```powershell
$env:PYO3_PYTHON = (Resolve-Path .venv\Scripts\python.exe).Path
$pythonBase = (& $env:PYO3_PYTHON -c "import sys; print(sys.base_prefix)").Trim()
$env:PATH = "$pythonBase;$env:PATH"
cargo fmt --check --manifest-path crates\docrt-core\Cargo.toml
cargo clippy --manifest-path crates\docrt-core\Cargo.toml -- -D warnings
cargo test --manifest-path crates\docrt-core\Cargo.toml
```

Office-bound local acceptance:

```powershell
uv run docrt doctor --agent --office-smoke
```
