# Storage Management

`docrt` writes runtime artifacts to ignored local directories:

- `logs/`
- `outputs/`
- `outputs/diagnostics/`
- `work/`
- `work/cache/`
- `state/`
- `dist/`

Inspect usage:

```powershell
uv run docrt storage-report
```

The report includes each target path, existence, file count, byte size, and
`oldest_file_time` so agents can decide whether age-based cleanup is safe.

`maintenance` combines storage reporting with recent error analysis, repair
planning, and writes small state snapshots under `state/`:

```powershell
uv run docrt maintenance
```

Plan cleanup without deleting:

```powershell
uv run docrt clean --logs --work --cache
uv run docrt clean --retention
uv run docrt clean --outputs --diagnostics --older-than 7
uv run docrt clean --all
```

`--retention` uses `log_retention_days`, `diagnostic_retention_days`, and
`cache_retention_days` from `docrt.config.json` or the default config. With no
target flags it plans only logs, diagnostics, and cache cleanup. Targets without
a retention policy, such as `outputs`, are skipped unless `--older-than` is also
provided.

By default, `clean` returns a compact summary and omits the full file list. Use
`--verbose` when an agent or maintainer needs to inspect every planned path:

```powershell
uv run docrt clean --logs --work --cache --verbose
uv run docrt clean --retention --verbose
```

Delete only after reviewing the dry-run result:

```powershell
uv run docrt clean --logs --work --cache --yes
uv run docrt clean --retention --yes
```

Run retention cleanup in the background when the exact result can be reviewed
later through `job-status`:

```powershell
uv run docrt job-start clean-retention
uv run docrt job-start clean-retention --yes
uv run docrt job-status <job-id>
```

The background command is also a dry-run unless `--yes` is provided.

`clean` refuses to delete targets outside the project root and does not follow
symlinked files.

## Optional Scheduled Cleanup

Create a Windows scheduled task manually if desired:

```powershell
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -Command `"Set-Location D:\project\python\codex-local-doc-runtime; uv run docrt clean --retention --yes`""
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 9am
Register-ScheduledTask -TaskName "docrt-clean-cache" -Action $Action -Trigger $Trigger
```

The project does not create scheduled tasks automatically.
