# ADR-0002: Require Local Microsoft Office COM

## Background

The target workflow is local Windows document automation for Codex / Agent use.
The user wants one fixed path for Word, PDF, and Excel processing rather than a
portable no-Office fallback matrix.

## Decision

Require local Microsoft Word and Microsoft Excel COM for mainline document
operations. `docrt` performs Office availability checks before public document
APIs dispatch work. Missing Office returns structured errors; main does not
currently implement a no-Office fallback.

## Reasons

- Word and Excel are the user's authoritative local document applications.
- A fixed runtime contract is easier for Agent workflows to reason about.
- High-fidelity DOCX/XLSX PDF export already requires Office COM.
- Failing early is clearer than silently changing behavior across machines.

## Advantages

- One predictable runtime path: Windows + uv + Office.
- Better alignment with local Office document rendering.
- Missing Office produces immediate structured diagnostics.

## Disadvantages

- Linux, macOS, WSL, Docker, and Windows without Office are not supported
  mainline targets for document processing.
- GitHub-hosted CI cannot prove real desktop Office success.
- Office COM automation still needs timeout and process cleanup diagnostics.

## Alternatives

- LibreOffice headless conversion: more portable, but not the requested fixed
  local Office path.
- Pure Python fallback: useful internally, but not accepted as public no-Office
  behavior for main.
- Cloud conversion APIs: introduce network, privacy, cost, and credentials.

## Impact

`doctor --agent` treats Word COM and Excel COM as required. Public document APIs
call runtime preflight before dispatching to internal Python modules such as
`python-docx`, PyMuPDF, and openpyxl. Those libraries are implementation
details after the required Office runtime is available, not a no-Office fallback
guarantee.
