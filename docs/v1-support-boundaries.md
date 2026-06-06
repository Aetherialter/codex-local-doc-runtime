# v1.1 Support Boundaries

`docrt` v1.1 is a Windows `uv` + local Microsoft Office runtime toolchain for
Agent workflows. It prioritizes one fixed local execution path over broad
headless portability.

## Supported Target

Mainline document processing requires:

- Windows 10/11.
- PowerShell.
- Git for source checkout recovery.
- `uv` as the required entrypoint.
- Microsoft Word desktop COM.
- Microsoft Excel desktop COM.
- Python dependencies declared in `pyproject.toml`.

Optional capabilities:

- Poppler for auxiliary PDF diagnostics.
- Rust core acceleration through a release wheel or local maturin build.

## uv Boundary

`uv` is required. If missing, docrt may attempt:

```powershell
winget install --id astral-sh.uv -e
```

If uv cannot be installed or does not appear on PATH, docrt reports
`UV_UNAVAILABLE` or `UV_BOOTSTRAP_FAILED`.

## Office Boundary

Word and Excel COM are required for the mainline runtime. Missing Office reports
structured errors and no no-Office fallback is implemented yet.

Possible errors:

- `OFFICE_COM_REQUIRED`
- `WORD_COM_UNAVAILABLE`
- `EXCEL_COM_UNAVAILABLE`

Interactive Office dialogs are not supported; first-run prompts, macro warnings,
privacy prompts, or repair prompts must be cleared by a user before automation
can be trusted.

## File Format Boundary

v1.1 supports `.docx`, `.pdf`, and `.xlsx` only within the required Windows +
uv + Office runtime.

Unsupported formats are explicit:

- `.doc` and `.xls`: `UNSUPPORTED_LEGACY_FORMAT`.
- Password-protected or encrypted Office/PDF files:
  `ENCRYPTED_FILE_UNSUPPORTED`.
- Damaged or unreadable supported containers: `CORRUPT_DOCUMENT` when the
  failure can be classified as document corruption.
- Unknown extensions or invalid containers: `UNSUPPORTED_FORMAT`.

## PDF Boundary

PDF support covers reading, inspection, rendering, text search, and additive
annotations. v1.1 does not support OCR or complex original-content editing.
Image-only PDFs report `needs_ocr=true` and `ocr_supported=false`.

## Rust Boundary

Rust is optional. Source checkouts continue to work without Rust by falling back
to Python for accelerated primitives. Rust must not become a separate workflow
dispatcher.

## CI Boundary

GitHub-hosted CI validates Python, Rust, JSON schema, CLI smoke, and structural
Office-boundary behavior on Windows. Real desktop Office success flows require
local validation or a self-hosted Windows runner through:

```powershell
uv run docrt doctor --agent --office-smoke
```
