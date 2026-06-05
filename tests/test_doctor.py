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


def test_poppler_lookup_returns_required_tools():
    tools = find_poppler_tools(Config.load())
    assert set(tools) == {"pdfinfo", "pdftoppm", "pdftocairo"}
