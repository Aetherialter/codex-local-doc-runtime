# v0.2.0-preview.1 - Lead Preview

This lead preview turns `codex-local-doc-runtime` into a more complete Windows
document runtime for Codex and other local agents.

## Highlights

- Adds DOCX heading-aware patching with `replace_heading`.
- Marks DOCX heading blocks in `read-docx` output with `style` and `is_heading`.
- Adds direct PDF text-layer search with `docrt search-pdf`.
- Keeps PDF support focused on reading, rendering, searching, and additive
  annotations, not complex original-content editing.
- Rewrites the README in Chinese with Windows, Office COM, Rust acceleration,
  cleanup, and clone recovery guidance.
- Documents a clean clone verification workflow for new Windows machines.

## Requirements

- Windows 10/11, PowerShell, Git, and uv are required for normal use.
- Microsoft Word is required for DOCX to PDF conversion.
- Microsoft Excel is required for XLSX to PDF conversion.
- Rust acceleration is optional and requires a local Rust toolchain plus
  `maturin develop`.

## Known Limitations

- No prebuilt Rust wheel is published yet. Without the native extension, `docrt`
  falls back to the Python core.
- GitHub Actions does not validate desktop Office COM conversion because
  Word/Excel are not assumed in CI.
- OCR, `.doc`, `.xls`, encrypted Office files, interactive Office dialogs, and
  complex PDF original-content editing are not supported.

## Verification

The release should be verified with:

```powershell
uv sync --dev
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv run docrt doctor --agent
uv run docrt agent-config
uv run docrt validate-patch examples\patches\docx-replace.json
uv run docrt patch-docx examples\fixtures\sample.docx examples\patches\docx-replace.json outputs\smoke\sample.heading.patched.docx --dry-run
uv run docrt search-pdf examples\fixtures\sample.pdf sample --output outputs\smoke\sample.pdf.search.json
```

Rust checks:

```powershell
$env:PYO3_PYTHON = (Resolve-Path .venv\Scripts\python.exe).Path
$pythonBase = (& $env:PYO3_PYTHON -c "import sys; print(sys.base_prefix)").Trim()
$env:PATH = "$pythonBase;$env:PATH"
cargo fmt --check --manifest-path crates\docrt-core\Cargo.toml
cargo clippy --manifest-path crates\docrt-core\Cargo.toml -- -D warnings
cargo test --manifest-path crates\docrt-core\Cargo.toml
```
