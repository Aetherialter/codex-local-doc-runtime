# Security Policy

## Supported Versions

Only the latest version on the default branch is actively maintained.

## Reporting a Vulnerability

Please open a private report through GitHub Security Advisories if the
repository is hosted on GitHub. If advisories are unavailable, open an issue
with minimal public detail and ask for a private contact path.

## Local File Safety

`docrt` processes local DOCX, PDF, and XLSX files. Treat untrusted documents as
potentially risky because parsing libraries and Microsoft Office automation may
exercise complex native code paths.

Recommended precautions:

- Run document conversion on files from trusted sources when possible.
- Keep Microsoft Office, Windows, and Python dependencies updated.
- Review generated files under `outputs/` before sharing them.
- Do not commit local `logs/`, `outputs/`, `work/`, or `docrt.config.json`.
