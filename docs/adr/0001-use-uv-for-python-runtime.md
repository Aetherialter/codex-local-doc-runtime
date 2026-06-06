# ADR-0001: Require uv for the Mainline Runtime

## Background

`docrt` is intended to be called by Codex / Agent workflows on a Windows machine.
The runtime should not depend on whatever global Python happens to be configured
on that machine.

## Decision

Require `uv run docrt ...` as the mainline entrypoint. If `uv` is missing and
`winget` is available, the runtime may bootstrap `uv` with:

```powershell
winget install --id astral-sh.uv -e
```

If automatic bootstrap fails, return a structured error such as
`UV_UNAVAILABLE` or `UV_BOOTSTRAP_FAILED`.

## Reasons

- Agent workflows need one reproducible invocation model.
- `uv.lock` gives deterministic dependency resolution for source checkouts.
- `uv run` avoids relying on global `python` or `py`.

## Advantages

- Reproducible setup through `uv.lock`.
- Consistent PowerShell-friendly commands for setup, testing, and CLI use.
- A missing uv installation has an explicit bootstrap path.

## Disadvantages

- The runtime is intentionally more opinionated than a generic Python package.
- Automatic bootstrap depends on `winget` and may require a new PowerShell
  session before `uv` appears on PATH.
- `.venv\Scripts\docrt.exe` is still not a standalone executable and cannot be
  copied away from the configured runtime directory.

## Alternatives

- `pip` plus `venv`: familiar, but less reproducible and too dependent on the
  user's global Python installation.
- Poetry: mature project workflow, but heavier than needed for this local
  runtime.
- End-user exe: out of scope for main; this branch stays a source-checkout
  runtime toolchain.

## Impact

README, `doctor`, `agent-config`, and runtime preflight all treat uv as required.
CI uses uv directly. Future exe or GUI distribution can wrap this behavior but
must not redefine main as a generic environment-manager-neutral SDK.
