import json
from pathlib import Path

import pytest

from docrt.config import Config
from docrt.models import ErrorCode
from docrt.paths import (
    ValidationError,
    default_inspect_output,
    normalize_path,
    path_resolution,
    validate_input_path,
)


def test_config_cli_timeout_override():
    config = Config.load(timeout=9)
    assert config.word_timeout_seconds == 9
    assert config.excel_timeout_seconds == 9
    assert config.poppler_timeout_seconds == 9


def test_config_load_coerces_legacy_numeric_strings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docrt.config.json").write_text(
        json.dumps({"log_retention_days": "7"}), encoding="utf-8"
    )

    config = Config.load(project_root=tmp_path)

    assert config.log_retention_days == 7


def test_config_load_rejects_invalid_numeric_strings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docrt.config.json").write_text(
        json.dumps({"log_retention_days": "soon"}), encoding="utf-8"
    )

    with pytest.raises(ValidationError) as exc_info:
        Config.load(project_root=tmp_path)

    assert exc_info.value.error_code == ErrorCode.VALIDATION_FAILED
    assert "log_retention_days" in str(exc_info.value)


def test_config_load_rejects_invalid_timeout_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DOCRT_TIMEOUT_SECONDS", "soon")

    with pytest.raises(ValidationError) as exc_info:
        Config.load()

    assert exc_info.value.error_code == ErrorCode.VALIDATION_FAILED
    assert "DOCRT_TIMEOUT_SECONDS" in str(exc_info.value)


def test_normalize_path_is_absolute(tmp_path):
    path = normalize_path(tmp_path / "file.txt")
    assert path.is_absolute()


def test_missing_file_is_classified(tmp_path: Path):
    with pytest.raises(ValidationError) as exc_info:
        validate_input_path(tmp_path / "missing.docx", {".docx"})
    assert exc_info.value.error_code == ErrorCode.FILE_NOT_FOUND
    message = str(exc_info.value)
    assert "original=" in message
    assert "cwd=" in message
    assert "expected_extensions=.docx" in message


def test_path_resolution_reports_relative_path_context(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = path_resolution("missing.docx")

    assert result["input"] == "missing.docx"
    assert result["is_absolute"] is False
    assert result["cwd"] == str(tmp_path)
    assert result["resolved"] == str((tmp_path / "missing.docx").resolve())
    assert result["exists"] is False


def test_unsupported_format_is_classified(tmp_path: Path):
    path = tmp_path / "file.txt"
    path.write_text("x", encoding="utf-8")
    with pytest.raises(ValidationError) as exc_info:
        validate_input_path(path, {".docx"})
    assert exc_info.value.error_code == ErrorCode.UNSUPPORTED_FORMAT


def test_default_inspect_output_keeps_extension_to_avoid_collisions(tmp_path: Path):
    outputs_dir = tmp_path / "outputs"

    docx_output = default_inspect_output(tmp_path / "sample.docx", outputs_dir)
    pdf_output = default_inspect_output(tmp_path / "sample.pdf", outputs_dir)
    xlsx_output = default_inspect_output(tmp_path / "sample.xlsx", outputs_dir)

    assert docx_output.name == "sample.docx.inspect.json"
    assert pdf_output.name == "sample.pdf.inspect.json"
    assert xlsx_output.name == "sample.xlsx.inspect.json"
    assert len({docx_output, pdf_output, xlsx_output}) == 3
