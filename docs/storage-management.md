# Storage Management

`docrt` writes runtime artifacts to ignored local directories:

- `logs/`
- `outputs/`
- `outputs/diagnostics/`
- `work/`
- `work/cache/`
- `dist/`

Inspect usage:

```powershell
uv run docrt storage-report
```

Plan cleanup without deleting:

```powershell
uv run docrt clean --logs --work --cache
uv run docrt clean --outputs --diagnostics --older-than 7
uv run docrt clean --all
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
