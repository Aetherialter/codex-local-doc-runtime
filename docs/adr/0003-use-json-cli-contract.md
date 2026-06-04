# ADR-0003: Use a Stable JSON CLI Contract

## Background

The runtime is intended for local automation, including agent-driven document
workflows. Human-readable output is useful, but automation needs predictable
machine-readable results.

## Decision

Every CLI command writes one normalized JSON result to stdout and records
structured logs under `logs/`.

## Reasons

A stable JSON contract lets callers inspect success, paths, backend details,
error codes, tracebacks, recovery actions, and diagnostics without scraping
terminal text.

## Advantages

- Easier integration with Codex and other automation tools.
- Consistent error handling across DOCX, PDF, XLSX, and doctor commands.
- Diagnostic files can be linked from the result object.

## Disadvantages

- Less friendly for casual terminal-only use.
- Backward compatibility matters once external users depend on the JSON shape.

## Alternatives

- Plain text CLI output: easier for humans, harder for automation.
- Mixed text and JSON output: convenient at first, but fragile for callers.
- Python-only API: useful for library users, but less convenient for tool-based
  local automation.

## Impact

Command output changes should be treated as API changes. Tests should cover the
result shape and error behavior when the JSON contract changes.
