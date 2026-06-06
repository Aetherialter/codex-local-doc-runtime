from __future__ import annotations

import json
import traceback as tb
from collections.abc import Callable
from pathlib import Path

from docrt.config import Config
from docrt.core_bridge import fingerprint, fingerprint_many, plan_batch, search_records
from docrt.docx_ops import inspect_docx
from docrt.errors import classify_exception, sanitize_text
from docrt.jsonutil import dump_file
from docrt.paths import SUPPORTED_EXTENSIONS, validate_input_path
from docrt.pdf_ops import inspect_pdf
from docrt.read_ops import read_docx, read_pdf, read_xlsx
from docrt.recovery import recovery_actions
from docrt.runtime_env import assert_mainline_runtime_for_path, confirmed_mainline_runtime
from docrt.xlsx_ops import inspect_xlsx


def fingerprint_file(path: str | Path) -> dict[str, object]:
    input_path = validate_input_path(path, SUPPORTED_EXTENSIONS)
    assert_mainline_runtime_for_path(input_path)
    return fingerprint(input_path)


def batch_fingerprint(paths: list[str | Path]) -> dict[str, object]:
    input_paths = [validate_input_path(path, SUPPORTED_EXTENSIONS) for path in paths]
    for input_path in input_paths:
        assert_mainline_runtime_for_path(input_path)
    return fingerprint_many(input_paths)


def cache_read(path: str | Path, config: Config) -> dict[str, object]:
    input_path = validate_input_path(path, SUPPORTED_EXTENSIONS)
    assert_mainline_runtime_for_path(input_path)
    with confirmed_mainline_runtime():
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
    return _batch_process(
        paths,
        lambda path: cache_read(path, config) if use_cache else _read_with_required_runtime(path),
    )


def batch_inspect(paths: list[str | Path]) -> dict[str, object]:
    return _batch_process(paths, _inspect_with_required_runtime)


def _batch_process(
    paths: list[str | Path],
    handler: Callable[[str | Path], dict[str, object]],
) -> dict[str, object]:
    plan = plan_batch(paths)
    results = []
    for item in plan["items"]:
        path = item["path"]
        try:
            result = handler(path)
            results.append({"path": str(path), "ok": True, "result": result})
        except Exception as exc:
            error_code = classify_exception(exc).value
            results.append(
                {
                    "path": str(path),
                    "ok": False,
                    "error": {
                        "error_code": error_code,
                        "error_message": sanitize_text(str(exc)),
                        "exception_type": type(exc).__name__,
                        "traceback": sanitize_text(tb.format_exc()),
                        "recovery_actions": recovery_actions(error_code),
                    },
                }
            )
    failed_count = sum(1 for result in results if not result["ok"])
    return {
        "count": len(results),
        "success_count": len(results) - failed_count,
        "failed_count": failed_count,
        "plan": plan,
        "results": results,
    }


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
        return {"query": query, "index_path": str(index_path), "backend": "none", "matches": []}
    data = json.loads(index_path.read_text(encoding="utf-8"))
    records = data.get("records", [])
    if not isinstance(records, list):
        records = []
    result = search_records(records, query)
    return {
        "query": query,
        "index_path": str(index_path),
        "backend": result["backend"],
        "count": result["count"],
        "matches": result["matches"],
    }


def _read_with_required_runtime(path: str | Path) -> dict[str, object]:
    input_path = validate_input_path(path, SUPPORTED_EXTENSIONS)
    assert_mainline_runtime_for_path(input_path)
    with confirmed_mainline_runtime():
        return _reader_for(input_path)(input_path)


def _inspect_with_required_runtime(path: str | Path) -> dict[str, object]:
    input_path = validate_input_path(path, SUPPORTED_EXTENSIONS)
    assert_mainline_runtime_for_path(input_path)
    with confirmed_mainline_runtime():
        return _inspector_for(input_path)(input_path)


def _reader_for(path: str | Path) -> Callable[[str | Path], dict[str, object]]:
    suffix = Path(path).suffix.lower()
    if suffix == ".docx":
        return read_docx
    if suffix == ".pdf":
        return read_pdf
    if suffix == ".xlsx":
        return read_xlsx
    raise ValueError(f"Unsupported format: {suffix}")


def _inspector_for(path: str | Path) -> Callable[[str | Path], dict[str, object]]:
    suffix = Path(path).suffix.lower()
    if suffix == ".docx":
        return inspect_docx
    if suffix == ".pdf":
        return inspect_pdf
    if suffix == ".xlsx":
        return inspect_xlsx
    raise ValueError(f"Unsupported format: {suffix}")
