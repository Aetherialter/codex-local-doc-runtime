from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from docrt.config import Config
from docrt.core_bridge import fingerprint, plan_batch
from docrt.jsonutil import dump_file
from docrt.paths import SUPPORTED_EXTENSIONS, validate_input_path
from docrt.read_ops import read_docx, read_pdf, read_xlsx


def fingerprint_file(path: str | Path) -> dict[str, object]:
    input_path = validate_input_path(path, SUPPORTED_EXTENSIONS)
    return fingerprint(input_path)


def cache_read(path: str | Path, config: Config) -> dict[str, object]:
    input_path = validate_input_path(path, SUPPORTED_EXTENSIONS)
    info = fingerprint(input_path)
    cache_path = config.work_path / "cache" / f"{info['sha256']}.read.json"
    if cache_path.exists():
        return {
            "cache_hit": True,
            "cache_path": str(cache_path),
            "fingerprint": info,
            "data": json.loads(cache_path.read_text(encoding="utf-8")),
        }
    data = _reader_for(input_path)(input_path)
    dump_file(cache_path, data)
    return {
        "cache_hit": False,
        "cache_path": str(cache_path),
        "fingerprint": info,
        "data": data,
    }


def batch_read(
    paths: list[str | Path], config: Config, *, use_cache: bool = False
) -> dict[str, object]:
    plan = plan_batch(paths)
    results = []
    for item in plan["items"]:
        path = item["path"]
        result = cache_read(path, config) if use_cache else _reader_for(Path(path))(path)
        results.append({"path": str(path), "ok": True, "result": result})
    return {"count": len(results), "plan": plan, "results": results}


def batch_inspect(paths: list[str | Path], config: Config) -> dict[str, object]:
    return batch_read(paths, config, use_cache=False)


def index(paths: list[str | Path], config: Config) -> dict[str, object]:
    records = []
    for path in paths:
        cached = cache_read(path, config)
        text = "\n".join(
            str(block.get("text", "")) for block in cached["data"].get("content_blocks", [])
        )
        records.append(
            {
                "path": str(path),
                "fingerprint": cached["fingerprint"],
                "text": text,
            }
        )
    index_path = config.work_path / "index" / "documents.json"
    dump_file(index_path, {"records": records})
    return {"index_path": str(index_path), "count": len(records)}


def search(query: str, config: Config) -> dict[str, object]:
    index_path = config.work_path / "index" / "documents.json"
    if not index_path.exists():
        return {"query": query, "index_path": str(index_path), "matches": []}
    data = json.loads(index_path.read_text(encoding="utf-8"))
    matches = []
    for record in data.get("records", []):
        text = str(record.get("text", ""))
        if query.lower() in text.lower():
            matches.append({"path": record.get("path"), "preview": _preview(text, query)})
    return {"query": query, "index_path": str(index_path), "matches": matches}


def _reader_for(path: str | Path) -> Callable[[str | Path], dict[str, object]]:
    suffix = Path(path).suffix.lower()
    if suffix == ".docx":
        return read_docx
    if suffix == ".pdf":
        return read_pdf
    if suffix == ".xlsx":
        return read_xlsx
    raise ValueError(f"Unsupported format: {suffix}")


def _preview(text: str, query: str, size: int = 120) -> str:
    position = text.lower().find(query.lower())
    if position < 0:
        return text[:size]
    start = max(0, position - size // 2)
    end = min(len(text), position + len(query) + size // 2)
    return text[start:end]
