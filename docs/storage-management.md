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
uv run docrt clean --outputs --diagnostics --older-than 7
uv run docrt clean --all
```

By default, `clean` returns a compact summary and omits the full file list. Use
`--verbose` when an agent or maintainer needs to inspect every planned path:

```powershell
uv run docrt clean --logs --work --cache --verbose
```

Delete only after reviewing the dry-run result:

```powershell
uv run docrt clean --logs --work --cache --yes
```

`clean` refuses to delete targets outside the project root and does not follow
symlinked files.

## Optional Scheduled Cleanup

Create a Windows scheduled task manually if desired:

```powershell
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -Command `"Set-Location D:\project\python\codex-local-doc-runtime; uv run docrt clean --logs --work --cache --older-than 14 --yes`""
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 9am
Register-ScheduledTask -TaskName "docrt-clean-cache" -Action $Action -Trigger $Trigger
```

The project does not create scheduled tasks automatically.
