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
- `UNSUPPORTED_LEGACY_FORMAT`: convert `.doc` to `.docx` or `.xls` to `.xlsx`
  before running `docrt`.
- `ENCRYPTED_FILE_UNSUPPORTED`: create an unencrypted copy before running
  `docrt`; do not place passwords in logs, task manifests, or patch files.
- `OCR_UNSUPPORTED`: run OCR outside `docrt` first. For image-only PDFs,
  `inspect-pdf` and `read-pdf` report `needs_ocr=true`.
- `PDF_ORIGINAL_EDIT_UNSUPPORTED`: use `annotate-pdf` for additive comments or
  marks; use a dedicated PDF editor for original-content editing.
- `FILE_LOCKED`: close Word, Excel, PDF readers, sync tools, or antivirus scans
  holding the file.
- `WORD_COM_UNAVAILABLE`: install Microsoft Word desktop edition and close
  interactive Word dialogs.
- `EXCEL_COM_UNAVAILABLE`: install Microsoft Excel desktop edition and close
  interactive Excel dialogs.
- `docx-to-pdf` and `xlsx-to-pdf` run a lightweight Office COM dispatch
  preflight before opening the input document. If this fails, run
  `uv run docrt doctor --agent --office-smoke` before retrying conversion.
- `POPPLER_UNAVAILABLE`: install Poppler or pass `--poppler-path`.
- `OFFICE_TIMEOUT`: retry with a larger `--timeout`.
- `WORD_CONVERSION_FAILED` / `EXCEL_CONVERSION_FAILED`: open the diagnostic
  JSON and inspect `error_event.context.worker_result`,
  `worker_stdout`, `worker_stderr`, and `office_process_cleanup` before retrying.
- `VALIDATION_FAILED`: validate patches and task manifests before execution.

## Diagnostic Flow

```powershell
Set-Location D:\project\python\codex-local-doc-runtime
uv run docrt doctor --office-smoke
uv run docrt validate-patch path\to\patch.json
uv run docrt validate-task path\to\task.json
```

If a command reports `diagnostic_report_path`, read that JSON before retrying.
For `FILE_NOT_FOUND`, inspect `error_event.context.path_resolution` and
`expected_extensions` in the diagnostic JSON. For task manifests, run
`uv run docrt explain-task <task.json>` and inspect `path_resolution`.

## Error Log Analysis

Failures are also written to daily JSONL files under `logs/errors/`. Use these
commands to summarize recent failures and generate repair suggestions:

```powershell
uv run docrt analyze-logs
uv run docrt analyze-logs --days 30 --limit 200
uv run docrt recent-errors --limit 20
uv run docrt repair-plan --days 30
uv run docrt maintenance
```

`analyze-logs` groups errors by `error_code` and operation, reports affected
modules, and emits suggested files plus validation commands for the next
maintenance pass.

`repair-plan` turns the analysis into a ranked next-action list with priority,
risk, target files, validation commands, and whether the fix requires human
confirmation. It writes `state/repair-plan.latest.json` by default and does not
auto-apply code changes.

If the same operation has a successful run after its latest error,
`repair-plan` marks the item as `status: observed_recovered`, includes
`last_success_at`, demotes it to `P4`, and disables auto-apply so historical
smoke failures remain visible without driving the next development pass.

`maintenance` stores the latest runtime, log-analysis, and repair-plan
summaries in `state/` so the next development pass can start from recent
evidence instead of relying on memory.

## Background Maintenance Jobs

Use background jobs only for low-risk maintenance tasks:

```powershell
uv run docrt job-start maintenance
uv run docrt job-start analyze-logs --days 30
uv run docrt job-start repair-plan --days 30
uv run docrt job-start clean-retention
uv run docrt job-status <job-id>
```

`job-start clean-retention` is a background dry-run by default. Add `--yes`
only after the retention cleanup plan is acceptable.

Background task failures are written to the same `logs/errors/*.error.jsonl`
stream and `outputs/diagnostics/*.job.diagnostic.json` files as foreground CLI
failures. The next `analyze-logs` or `repair-plan` run can therefore include
background failures in the repair backlog.

Document editing and conversion remain foreground operations in v1.0 so
users can see the exact JSON result before trusting the output file.
