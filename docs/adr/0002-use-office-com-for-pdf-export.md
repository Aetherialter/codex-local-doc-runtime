# ADR-0002: Use Microsoft Office COM for DOCX and XLSX PDF Export

## Background

DOCX and XLSX to PDF conversion quality depends heavily on layout fidelity.
Pure Python libraries can inspect these formats, but they do not reliably match
Microsoft Office rendering.

## Decision

Use Microsoft Word COM for DOCX to PDF and Microsoft Excel COM for XLSX to PDF
on Windows.

## Reasons

Office COM uses the same desktop applications that users commonly rely on for
final document rendering, which improves layout fidelity for local automation.

## Advantages

- Better fidelity for complex Word and Excel layouts.
- Direct support for common Office documents on Windows.
- Clear operational boundary: Office-dependent features are diagnosed by
  `docrt doctor`.

## Disadvantages

- Requires Microsoft Office on the target machine.
- Only works on Windows.
- COM automation can leave processes behind if conversion fails unexpectedly, so
  the project needs process diagnostics and careful cleanup behavior.

## Alternatives

- LibreOffice headless conversion: more portable, but not always faithful to
  Microsoft Office layouts.
- Cloud conversion APIs: simpler operations, but introduces network, privacy,
  cost, and credential concerns.
- Pure Python conversion: avoids desktop dependencies, but does not provide
  reliable PDF export fidelity.

## Impact

Office conversion is isolated in subprocess workers, guarded by timeouts, and
paired with process diagnostics. CI avoids relying on Office-specific conversion
success.
