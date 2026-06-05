# ADR-0006: Add an Agent Integration Contract

## Background

The runtime is meant to be called by Codex and other local agents, but README
instructions alone are not a stable machine-readable contract. Agents need a
repeatable way to discover the preferred path, supported commands, environment
readiness, task effects, and cleanup workflow.

## Decision

Add three Agent-facing commands:

- `docrt agent-config` emits a JSON object with runtime metadata, bootstrap
  commands, common command groups, unsupported capabilities, and a reusable
  `AGENTS.md` Markdown fragment.
- `docrt doctor --agent` adds Agent readiness checks to the normal doctor JSON,
  including writable runtime paths and optional Office/Poppler/Rust status.
- `docrt explain-task` describes task manifest effects before execution,
  including files read, files written, generated artifacts, Office COM need,
  and dry-run support.

## Reasons

These commands turn project documentation into executable checks and structured
metadata. They reduce the chance that an agent silently falls back to temporary
scripts or stale instructions.

## Advantages

- Codex can discover and reuse the same local document workflow across projects.
- Migration to a new Windows machine has an explicit recovery path.
- Task manifests can be reviewed before they modify documents.
- The JSON contract remains scriptable while still carrying a human-copyable
  Markdown fragment.

## Disadvantages

- The CLI surface grows and must stay backward compatible.
- Agent readiness can only report optional desktop dependencies such as Office
  COM and Poppler; it cannot make them available in CI.
- The generated Markdown fragment must be kept in sync with real CLI behavior.

## Alternatives

- README-only integration: simpler, but agents must infer behavior from prose.
- Global Codex instructions only: useful on one machine, but less portable for
  open-source users.
- Hidden Python API: easier to change, but less useful to CLI-based agents.

## Impact

Tests and CI should cover the Agent commands as part of the public contract.
Future changes to command names, task manifest fields, or storage paths should
update `agent-config`, `docs/codex-integration.md`, `examples/AGENTS.template.md`,
and this ADR if the integration model changes.
