# ADR-0004: Defer Rust Core Until Document Protocols Stabilize

Status: Superseded by ADR-0005.

## Background

The project may eventually use a Rust core for file fingerprinting, hash cache,
diff calculation, patch validation, and batch planning. The current priority is
to stabilize the Python CLI protocol used by agents.

## Decision

Do not introduce Rust in the current phase. Keep Python as the only runtime
implementation until read, patch, verify, and task manifest protocols have
settled.

## Reasons

The Python layer already owns Office COM, PyMuPDF, python-docx, openpyxl, CLI
composition, logging, and diagnostics. Adding Rust before the protocol is stable
would increase packaging and maintenance cost without removing current
uncertainty.

## Advantages

- Keeps installation simple for Windows users.
- Keeps CI and local development focused on one runtime.
- Allows CLI JSON contracts to evolve before freezing Rust/Python bindings.
- Avoids introducing maturin or pyo3 before there is a clear performance need.

## Disadvantages

- Batch scanning, hashing, and diff operations remain Python-only for now.
- Future Rust integration will require a migration step and new build tooling.

## Alternatives

- Add Rust immediately with pyo3 and maturin: rejected because protocol churn is
  still expected.
- Never add Rust: rejected because future large-document and batch workflows may
  benefit from Rust's performance and stronger schema validation.

## Impact

Rust will be reconsidered after the Python read, patch, verify, and run-task
commands are stable and covered by tests. Any future Rust integration must have
its own ADR and preserve a clear failure mode when Rust components are
unavailable.
