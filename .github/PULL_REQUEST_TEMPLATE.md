## Summary

Describe the change and why it is needed.

## Validation

Run the relevant commands and paste the results:

```powershell
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv run docrt doctor --agent --office-smoke
uv run docrt agent-config
```

## Checklist

- [ ] CLI JSON output remains stable or the README explains the change.
- [ ] Tests cover the changed behavior.
- [ ] README or docs are updated for user-facing changes.
- [ ] Office COM behavior was tested locally when conversion code changed.
