from docrt.config import Config
from docrt.doctor import doctor_report, find_poppler_tools


def test_doctor_report_shape():
    report = doctor_report(Config.load())
    assert "packages" in report
    assert "office" in report
    assert "poppler" in report
    assert "core" in report


def test_doctor_report_office_smoke_shape(monkeypatch):
    monkeypatch.setattr("docrt.doctor.check_word_com", lambda: True)
    monkeypatch.setattr("docrt.doctor.check_excel_com", lambda: True)

    report = doctor_report(Config.load(), office_smoke=True)

    assert "office_smoke" in report
    assert report["office_smoke"]["interactive_dialogs_checked"] is False


def test_doctor_report_office_smoke_uses_dispatch_checks(monkeypatch):
    monkeypatch.setattr("docrt.doctor.check_word_com", lambda: True)
    monkeypatch.setattr("docrt.doctor.check_excel_com", lambda: False)

    report = doctor_report(Config.load(), office_smoke=True)

    assert report["office_smoke"]["word_dispatch"] is True
    assert report["office_smoke"]["excel_dispatch"] is False


def test_doctor_report_agent_block(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='docrt-test'\n", encoding="utf-8")
    (tmp_path / "src" / "docrt").mkdir(parents=True)
    monkeypatch.setattr("docrt.doctor.check_word_com", lambda: False)
    monkeypatch.setattr("docrt.doctor.check_excel_com", lambda: False)

    report = doctor_report(Config.load(project_root=tmp_path), agent=True)

    assert "agent" in report
    assert report["agent"]["in_docrt_project"] is True
    assert report["agent"]["required"]["paths_writable"]["outputs"] is True
    assert report["agent"]["ready"] is False
    assert report["agent"]["required"]["word_com_available"] is False
    assert report["agent"]["required"]["excel_com_available"] is False
    assert report["agent"]["recommended_doctor_command"] == (
        "uv run docrt doctor --agent --office-smoke"
    )


def test_agent_ready_requires_pywin32(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='docrt-test'\n", encoding="utf-8")
    (tmp_path / "src" / "docrt").mkdir(parents=True)
    monkeypatch.setattr("docrt.doctor.check_word_com", lambda: False)
    monkeypatch.setattr("docrt.doctor.check_excel_com", lambda: False)

    def fake_check_import(module_name: str) -> bool:
        return module_name != "win32com.client"

    monkeypatch.setattr("docrt.doctor.check_import", fake_check_import)

    report = doctor_report(Config.load(project_root=tmp_path), agent=True)

    assert report["packages"]["pywin32"]["available"] is False
    assert report["agent"]["required"]["packages"]["pywin32"] is False
    assert "pywin32" not in report["agent"]["optional"]["packages"]
    assert report["agent"]["ready"] is False


def test_poppler_lookup_returns_required_tools():
    tools = find_poppler_tools(Config.load())
    assert set(tools) == {"pdfinfo", "pdftoppm", "pdftocairo"}
