# v0.2.0-preview.2 - Lead Preview Workflow Fix

This preview keeps the `v0.2.0-preview.1` runtime behavior and fixes the GitHub
release workflow.

## Fixed

- Makes the GitHub release workflow idempotent.
- If a prerelease already exists for the pushed tag, the workflow now updates it
  with `gh release edit` instead of failing on `gh release create`.

## Runtime Status

- DOCX heading-aware patching remains available through `replace_heading`.
- PDF support remains focused on reading, rendering, text search, and additive
  annotations, not complex original-content editing.
- Office COM conversion still requires Microsoft Word or Microsoft Excel on the
  local Windows machine.
- Rust acceleration is still optional. No prebuilt wheel is published yet; users
  can enable the native extension locally with Rust and maturin, otherwise
  `docrt` falls back to the Python core.

## Verification

Verified locally on Windows with:

```powershell
uv sync --dev
uv run ruff format --check .
uv run ruff check .
uv run pytest
cargo fmt --check --manifest-path crates\docrt-core\Cargo.toml
cargo clippy --manifest-path crates\docrt-core\Cargo.toml -- -D warnings
cargo test --manifest-path crates\docrt-core\Cargo.toml
uv run docrt doctor --agent
```
