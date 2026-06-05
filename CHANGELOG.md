# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog style, and this project uses semantic
versioning.

## [0.2.0-preview.1] - 2026-06-05

### Added

- Lead preview release for the Windows Codex local document runtime.
- DOCX `replace_heading` patch operation targeting heading text, heading style,
  or both.
- DOCX read output now marks heading blocks with `style` and `is_heading`.
- Direct PDF text-layer search through `docrt search-pdf`.
- Chinese README with explicit Windows, Office COM, Rust acceleration, cleanup,
  and clean clone verification guidance.

### Known Limitations

- Office COM conversion requires Microsoft Word or Microsoft Excel installed on
  the local Windows machine.
- GitHub Actions does not validate desktop Office COM flows.
- Rust acceleration is available but no prebuilt wheel is published yet; users
  need Rust and maturin locally to enable the native extension.
- Without the Rust extension, `docrt` falls back to the Python core.
- PDF support covers reading, rendering, text search, and additive annotations,
  not complex original-content editing.

## [0.1.0] - 2026-06-04

### Added

- Initial Windows-first `docrt` CLI for DOCX, PDF, and XLSX processing.
- JSON result contract for all operations.
- DOCX inspection and Word COM based PDF export.
- PDF inspection and rendering with PyMuPDF.
- XLSX inspection and Excel COM based PDF export.
- Runtime doctor command for package, Office COM, Poppler, and path diagnostics.
- Structured JSONL logs and diagnostic report paths.
