# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog style, and this project uses semantic
versioning.

## [1.0.0] - 2026-06-06

### Added

- Stable v1.0 Windows-first release for Agent local DOCX/PDF/XLSX workflows.
- Explicit v1.0 support matrix covering Windows, Office COM, Linux/macOS, Docker,
  OCR, PDF editing, and Rust acceleration boundaries.
- Structured unsupported-boundary error codes for legacy Office formats,
  encrypted files, OCR gaps, PDF original-content editing, and interactive
  Office dialog workflows.
- Release workflow that builds Python artifacts and a Windows Rust extension
  wheel from `v*` tags.

### Changed

- Promote the Python package to `1.0.0` and mark the project as stable.
- Promote `docrt-core` crate metadata to `1.0.0`.
- PDF inspection and reading now expose `needs_ocr`, `ocr_supported`, and
  encryption metadata.
- `repair-plan` treats historical issues with later successful runs as
  `observed_recovered` P4 monitoring items.

### Known Limitations

- v1.0 remains Windows-first. Non-Office functionality may run on Linux/macOS,
  but the supported target is Windows + PowerShell + uv.
- DOCX/XLSX to PDF conversion requires desktop Microsoft Word or Excel.
- Desktop Office COM flows cannot be fully covered by GitHub-hosted CI.
- OCR, `.doc`, `.xls`, encrypted files, interactive Office dialogs, and complex
  PDF original-content editing are intentionally unsupported in v1.0.

## [0.2.0-preview.2] - 2026-06-05

### Fixed

- Make the GitHub release workflow idempotent so re-running or re-publishing a
  tag updates the existing prerelease instead of failing when the release
  already exists.

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
