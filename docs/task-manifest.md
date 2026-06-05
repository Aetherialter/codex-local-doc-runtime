# Task Manifest

`run-task` executes one document operation from a JSON manifest. This gives
agents a stable, replayable command format.

Command:

```powershell
uv run docrt run-task task.json
```

## Common Fields

```json
{
  "task": "read-docx",
  "input": "examples/fixtures/sample.docx",
  "output": "outputs/tasks/sample.read.json",
  "dry_run": false
}
```

Supported tasks:

- `inspect-docx`
- `inspect-pdf`
- `inspect-xlsx`
- `read-docx`
- `read-pdf`
- `read-xlsx`
- `patch-docx`
- `patch-xlsx`
- `docx-to-pdf`
- `xlsx-to-pdf`
- `render-pdf`

## Dry Run

```json
{
  "task": "patch-xlsx",
  "input": "examples/fixtures/sample.xlsx",
  "patch": "work/patch.xlsx.json",
  "output": "outputs/tasks/sample.patched.xlsx",
  "dry_run": true
}
```

Dry run validates the task name and required top-level shape, then reports what
would be executed without modifying documents.

## Patch Task

```json
{
  "task": "patch-docx",
  "input": "examples/fixtures/sample.docx",
  "patch": "work/patch.docx.json",
  "output": "outputs/tasks/sample.patched.docx"
}
```

Failures use the same JSON result error fields as direct CLI commands, including
`error_code`, `error_message`, `log_path`, and `diagnostic_report_path`.
