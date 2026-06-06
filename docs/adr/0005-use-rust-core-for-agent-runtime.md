# ADR-0005: Use Rust Core For Agent Runtime

## Background

`docrt` needs a stable CLI surface for Agent document workflows and a small set
of performance-sensitive, safety-sensitive primitives that will be called often:
file fingerprinting, batch fingerprinting, indexed search, path containment
checks, JSON preflight validation, and batch planning.

## Decision

Keep Python as the orchestration layer for runtime preflight, direct document
operation dispatch, Office COM, PyMuPDF, python-docx, and openpyxl. Keep the
Rust extension crate at `crates/docrt-core` as an optional service layer using
PyO3 and maturin. Python calls the Rust extension through `docrt.core_bridge`
and falls back to pure Python when the native module is not built.

## Reasons

Rust is a good fit for deterministic file hashing, batch file scanning, simple
text search over existing indexes, path normalization, manifest validation
primitives, and future OOXML container preflight. Python remains the better
integration layer for runtime policy, structured errors, Windows Office
automation, and the existing document libraries.

## Pros

- Keeps the public CLI stable while allowing native acceleration.
- Makes path and cache operations easier to harden over time.
- Allows source checkout usage before the Rust extension is compiled.
- Preserves the same Python API behavior across Rust and Python fallback modes.

## Cons

- Adds a Rust toolchain requirement for native builds.
- Adds another build path to CI and release validation.
- Requires careful fallback tests so the CLI does not silently depend on Rust.

## Alternatives

- Pure Python only: simpler build, but less headroom for batch/cache-heavy
  workflows.
- Full Rust rewrite: larger risk and poor fit for Office COM automation.
- Rust sidecar executable: easier isolation, but more process overhead and a
  less direct Python integration story.

## Impact

The repository now has a hybrid structure. Recommended source checkout
execution still uses `uv run docrt ...`; native acceleration is enabled with
`uv run maturin develop --manifest-path crates\docrt-core\Cargo.toml`. The Rust
extension must stay below `docrt.core_bridge` and must not become a second
workflow dispatcher.
