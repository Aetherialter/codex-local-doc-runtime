from __future__ import annotations

from pathlib import Path

import pytest

from docrt import core_bridge
from docrt.paths import ValidationError


def test_core_bridge_fingerprint_and_hash(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("hello docrt", encoding="utf-8")

    digest = core_bridge.sha256_file(sample)
    fingerprint = core_bridge.fingerprint(sample)

    assert len(digest) == 64
    assert fingerprint["sha256"] == digest
    assert fingerprint["size"] == len("hello docrt")
    assert fingerprint["backend"] in {"python", "rust"}


def test_core_bridge_path_safety(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    inside = root / "inside.txt"
    outside = tmp_path / "outside.txt"
    inside.write_text("inside", encoding="utf-8")
    outside.write_text("outside", encoding="utf-8")

    assert core_bridge.is_path_within_root(root, inside) is True
    assert core_bridge.is_path_within_root(root, outside) is False


def test_core_bridge_json_object_validation() -> None:
    assert core_bridge.validate_basic_json_object('{"ok": true}') is True
    with pytest.raises(ValidationError):
        core_bridge.validate_basic_json_object("[1, 2, 3]")


def test_core_bridge_python_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("fallback", encoding="utf-8")
    monkeypatch.setattr(core_bridge, "_rust_core", None)

    assert core_bridge.backend() == "python"
    assert core_bridge.fingerprint(sample)["backend"] == "python"
    assert core_bridge.fingerprint_many([sample])["backend"] == "python"
    assert core_bridge.validate_basic_json_object('{"fallback": true}') is True
    assert core_bridge.plan_batch([sample])["backend"] == "python"
    assert (
        core_bridge.search_records(
            [{"path": str(sample), "text": "fallback search target"}], "target"
        )["backend"]
        == "python"
    )


def test_core_bridge_batch_planner(tmp_path: Path) -> None:
    first = tmp_path / "first.docx"
    second = tmp_path / "second.xlsx"

    result = core_bridge.plan_batch([first, second])

    assert result["backend"] in {"python", "rust"}
    assert result["count"] == 2
    assert result["items"][0]["index"] == 0


def test_core_bridge_batch_fingerprint(tmp_path: Path) -> None:
    first = tmp_path / "first.docx"
    second = tmp_path / "second.xlsx"
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")

    result = core_bridge.fingerprint_many([first, second])

    assert result["backend"] in {"python", "rust"}
    assert result["count"] == 2
    assert result["items"][0]["sha256"]
    assert result["items"][0]["path"] == str(first)


def test_core_bridge_search_records() -> None:
    records = [
        {"path": "a.docx", "text": "alpha needle omega"},
        {"path": "b.docx", "text": "plain text"},
    ]

    result = core_bridge.search_records(records, "needle")

    assert result["backend"] in {"python", "rust"}
    assert result["count"] == 1
    assert result["matches"][0]["path"] == "a.docx"
    assert "needle" in result["matches"][0]["preview"]
