# Batch And Cache Design

Batch and cache commands are designed for Agent workflows that repeatedly read
the same local documents.

## Commands

```powershell
uv run docrt fingerprint path\to\file.docx
uv run docrt batch-fingerprint path\to\a.docx path\to\b.xlsx
uv run docrt cache-read path\to\file.docx
uv run docrt batch-read path\to\a.docx path\to\b.pdf --use-cache
uv run docrt batch-inspect path\to\a.docx path\to\b.xlsx
uv run docrt index path\to\a.docx path\to\b.xlsx
uv run docrt search "keyword"
```

`fingerprint`, `batch-fingerprint`, and indexed `search` use the Rust core when
available and fall back to Python when the native extension is not built.

`batch-read` returns read output and can use `--use-cache`. `batch-inspect`
returns structural inspection output and does not use the read cache.

Both batch commands isolate per-file failures. A missing or invalid file
produces an item-level `error` object and increments `failed_count`, while
successful files still return their results.

## Cache Location

Read caches are stored under:

```text
work/cache/
```

The cache is ignored by Git and can be inspected or cleaned with:

```powershell
uv run docrt storage-report
uv run docrt clean --cache
uv run docrt clean --cache --yes
```

`clean` is dry-run by default. It only deletes when `--yes` is present.
