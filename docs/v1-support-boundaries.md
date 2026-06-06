# v1.0 Support Boundaries

`docrt` v1.0 is a Windows-first local document runtime for Agent workflows. It
prioritizes explicit capability detection, structured errors, reproducible JSON
results, and safe local artifact management over broad platform claims.

## Supported Target

- Windows 10/11.
- PowerShell.
- Git and uv.
- Python 3.12 managed by uv.
- Optional Microsoft Word desktop edition for DOCX to PDF conversion.
- Optional Microsoft Excel desktop edition for XLSX to PDF conversion.
- Optional Poppler for auxiliary PDF diagnostics.
- Optional Rust core acceleration through a release wheel or local maturin
  build.

## Portability

Non-Office features are designed to avoid direct Windows APIs where practical,
but v1.0 validation and release gates are Windows-first. Linux, macOS, and
Docker usage is best-effort for non-Office commands and is not the primary
support target.

## Office COM Boundary

DOCX/XLSX to PDF conversion depends on desktop Microsoft Office COM automation.
If Word or Excel is unavailable, commands fail with `WORD_COM_UNAVAILABLE` or
`EXCEL_COM_UNAVAILABLE`. Interactive Office dialogs are not supported; first-run
prompts, macro warnings, privacy prompts, or repair prompts must be cleared by a
user before automation can be trusted.

## File Format Boundary

v1.0 supports `.docx`, `.pdf`, and `.xlsx`.

Unsupported formats are explicit:

- `.doc` and `.xls`: `UNSUPPORTED_LEGACY_FORMAT`.
- Password-protected or encrypted Office/PDF files:
  `ENCRYPTED_FILE_UNSUPPORTED`.
- Unknown extensions or invalid containers: `UNSUPPORTED_FORMAT`.

## PDF Boundary

PDF support covers reading, inspection, rendering, text search, and additive
annotations. v1.0 does not support OCR or complex original-content editing.
Image-only PDFs report `needs_ocr=true` and `ocr_supported=false`.

## Rust Boundary

The Rust core is an optional acceleration layer. v1.0 release automation builds
a Windows extension wheel, but source checkouts continue to work without Rust by
falling back to Python.

## CI Boundary

GitHub-hosted CI covers Python, Rust, JSON schema, CLI smoke, and non-Office
document workflows. Desktop Office COM flows require local validation through:

```powershell
uv run docrt doctor --agent --office-smoke
```
