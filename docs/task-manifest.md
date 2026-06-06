# Task Manifest

`run-task` executes one or more document operations from a JSON manifest. This
gives agents a stable, replayable command format.

Command:

```powershell
uv run docrt run-task task.json
```

Explain a manifest before execution:

```powershell
uv run docrt explain-task task.json
```

`explain-task` returns JSON describing files that will be read, modified, or
generated, whether Office COM is required, whether intermediate artifacts may be
created, and whether every step supports dry-run planning.

`supports_native_dry_run` means the underlying operation can validate and plan
without writing output files. In this preview, only `patch-docx` and
`patch-xlsx` are native dry-run operations. Other tasks use plan-only dry-run
at the task-manifest layer.

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
- `verify-docx`
- `verify-xlsx`
- `docx-to-pdf`
- `xlsx-to-pdf`
- `render-pdf`
- `search-pdf`

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

## PDF Search Task

```json
{
  "task": "search-pdf",
  "input": "examples/fixtures/sample.pdf",
  "query": "sample",
  "pages": "1,3-5",
  "output": "outputs/tasks/sample.pdf.search.json"
}
```

PDF `read-pdf`, `render-pdf`, and `search-pdf` support `pages` using 1-based
page numbers such as `"1"`, `"1-3"`, or `"1,3-5"`.

Failures use the same JSON result error fields as direct CLI commands, including
`error_code`, `error_message`, `log_path`, and `diagnostic_report_path`.

## Multi-Step Workflow

```json
{
  "stop_on_error": true,
  "tasks": [
    {
      "id": "patch",
      "task": "patch-xlsx",
      "input": "examples/fixtures/sample.xlsx",
      "patch": "work/patch.xlsx.json",
      "output": "outputs/tasks/sample.patched.xlsx"
    },
    {
      "id": "verify",
      "task": "verify-xlsx",
      "before": "examples/fixtures/sample.xlsx",
      "after": "${steps.patch.output_path}"
    }
  ]
}
```

Step references use this form:

```text
${steps.<id>.<field>}
```

The final result contains `steps`, `success_count`, and `failed_count`. Step
failures include `recovery_actions`.
