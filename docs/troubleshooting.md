# Troubleshooting

All `docrt` commands return one JSON result. On failure, inspect these fields
before changing the command:

- `error_code`
- `error_message`
- `recovery_actions`
- `diagnostic_report_path`
- `log_path`

## Common Error Codes

- `FILE_NOT_FOUND`: check the path and current working directory.
- `UNSUPPORTED_FORMAT`: use `.docx`, `.pdf`, or `.xlsx`.
- `FILE_LOCKED`: close Word, Excel, PDF readers, sync tools, or antivirus scans
  holding the file.
- `WORD_COM_UNAVAILABLE`: install Microsoft Word desktop edition and close
  interactive Word dialogs.
- `EXCEL_COM_UNAVAILABLE`: install Microsoft Excel desktop edition and close
  interactive Excel dialogs.
- `POPPLER_UNAVAILABLE`: install Poppler or pass `--poppler-path`.
- `OFFICE_TIMEOUT`: retry with a larger `--timeout`.
- `VALIDATION_FAILED`: validate patches and task manifests before execution.

## Diagnostic Flow

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv run docrt doctor --office-smoke
uv run docrt validate-patch path\to\patch.json
uv run docrt validate-task path\to\task.json
```

If a command reports `diagnostic_report_path`, read that JSON before retrying.

## Error Log Analysis

Failures are also written to daily JSONL files under `logs/errors/`. Use these
commands to summarize recent failures and generate repair suggestions:

```powershell
uv run docrt analyze-logs
uv run docrt analyze-logs --days 30 --limit 200
uv run docrt recent-errors --limit 20
```

`analyze-logs` groups errors by `error_code` and operation, reports affected
modules, and emits suggested files plus validation commands for the next
maintenance pass.
