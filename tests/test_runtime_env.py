from __future__ import annotations

from docrt.models import ErrorCode
from docrt.paths import ValidationError
from docrt.read_ops import read_docx
from docrt.runtime_env import (
    _RUNTIME_PREFLIGHT_CONFIRMED,
    assert_mainline_runtime_for_path,
    ensure_mainline_runtime,
    ensure_office_available,
    ensure_uv_available,
)


def test_ensure_uv_available_reports_existing_uv(monkeypatch) -> None:
    monkeypatch.setattr("docrt.runtime_env.shutil.which", lambda name: "C:\\uv.exe")

    result = ensure_uv_available(auto_install=False)

    assert result["available"] is True
    assert result["path"] == "C:\\uv.exe"
    assert result["installed"] is False


def test_ensure_uv_available_can_fail_without_auto_install(monkeypatch) -> None:
    monkeypatch.setattr("docrt.runtime_env.shutil.which", lambda _name: None)

    try:
        ensure_uv_available(auto_install=False)
    except ValidationError as exc:
        assert exc.error_code == ErrorCode.UV_UNAVAILABLE
        assert exc.context["required_entrypoint"] == "uv run docrt"
    else:  # pragma: no cover
        raise AssertionError("expected UV_UNAVAILABLE")


def test_ensure_uv_available_reports_bootstrap_failure_without_winget(monkeypatch) -> None:
    monkeypatch.setattr("docrt.runtime_env.shutil.which", lambda _name: None)

    try:
        ensure_uv_available(auto_install=True)
    except ValidationError as exc:
        assert exc.error_code == ErrorCode.UV_BOOTSTRAP_FAILED
        assert exc.context["winget_available"] is False
    else:  # pragma: no cover
        raise AssertionError("expected UV_BOOTSTRAP_FAILED")


def test_ensure_office_available_requires_word_and_excel(monkeypatch) -> None:
    monkeypatch.setattr("docrt.runtime_env.check_word_com", lambda: False)
    monkeypatch.setattr("docrt.runtime_env.check_excel_com", lambda: False)

    try:
        ensure_office_available()
    except ValidationError as exc:
        assert exc.error_code == ErrorCode.OFFICE_COM_REQUIRED
        assert exc.context["missing"] == ["Microsoft Word COM", "Microsoft Excel COM"]
        assert exc.context["current_solution"] == "no_fallback_yet"
    else:  # pragma: no cover
        raise AssertionError("expected OFFICE_COM_REQUIRED")


def test_ensure_mainline_runtime_reports_required_shape(monkeypatch) -> None:
    monkeypatch.setattr("docrt.runtime_env.shutil.which", lambda name: f"C:\\{name}.exe")
    monkeypatch.setattr("docrt.runtime_env.check_word_com", lambda: True)
    monkeypatch.setattr("docrt.runtime_env.check_excel_com", lambda: True)

    result = ensure_mainline_runtime()

    assert result["runtime"] == "uv_plus_local_office"
    assert result["uv"]["available"] is True
    assert result["office"]["word_com_available"] is True
    assert result["rust"] == "optional_acceleration_with_python_fallback"


def test_direct_document_preflight_can_fail_without_office(monkeypatch, tmp_path) -> None:
    sample = tmp_path / "sample.pdf"
    sample.write_bytes(b"%PDF-1.4\n%%EOF\n")
    monkeypatch.setattr(
        "docrt.runtime_env.shutil.which", lambda name: "uv.exe" if name == "uv" else None
    )
    monkeypatch.setattr("docrt.runtime_env.check_word_com", lambda: False)
    monkeypatch.setattr("docrt.runtime_env.check_excel_com", lambda: False)

    token = _RUNTIME_PREFLIGHT_CONFIRMED.set(False)
    try:
        try:
            assert_mainline_runtime_for_path(sample)
        except ValidationError as exc:
            assert exc.error_code == ErrorCode.OFFICE_COM_REQUIRED
        else:  # pragma: no cover
            raise AssertionError("expected OFFICE_COM_REQUIRED")
    finally:
        _RUNTIME_PREFLIGHT_CONFIRMED.reset(token)


def test_direct_low_level_read_fails_without_office(monkeypatch, tmp_path) -> None:
    from docx import Document

    sample = tmp_path / "sample.docx"
    document = Document()
    document.add_paragraph("hello")
    document.save(sample)
    monkeypatch.setattr(
        "docrt.runtime_env.shutil.which", lambda name: "uv.exe" if name == "uv" else None
    )
    monkeypatch.setattr("docrt.runtime_env.check_word_com", lambda: False)
    monkeypatch.setattr("docrt.runtime_env.check_excel_com", lambda: False)

    token = _RUNTIME_PREFLIGHT_CONFIRMED.set(False)
    try:
        try:
            read_docx(sample)
        except ValidationError as exc:
            assert exc.error_code == ErrorCode.OFFICE_COM_REQUIRED
        else:  # pragma: no cover
            raise AssertionError("expected OFFICE_COM_REQUIRED")
    finally:
        _RUNTIME_PREFLIGHT_CONFIRMED.reset(token)
