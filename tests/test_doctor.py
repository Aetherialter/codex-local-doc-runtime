from docrt.config import Config
from docrt.doctor import doctor_report, find_poppler_tools


def test_doctor_report_shape():
    report = doctor_report(Config.load())
    assert "packages" in report
    assert "office" in report
    assert "poppler" in report


def test_poppler_lookup_returns_required_tools():
    tools = find_poppler_tools(Config.load())
    assert set(tools) == {"pdfinfo", "pdftoppm", "pdftocairo"}
