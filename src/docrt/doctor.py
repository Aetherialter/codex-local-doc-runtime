from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

from docrt import core_bridge
from docrt.config import Config

PYTHON_PACKAGES = {
    "python-docx": "docx",
    "pywin32": "win32com.client",
    "PyMuPDF": "fitz",
    "openpyxl": "openpyxl",
    "pandas": "pandas",
    "psutil": "psutil",
    "pytest": "pytest",
}

POPPLER_TOOLS = ("pdfinfo", "pdftoppm", "pdftocairo")


def check_import(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except ModuleNotFoundError:
        return False


def check_word_com() -> bool:
    return _check_com("Word.Application")


def check_excel_com() -> bool:
    return _check_com("Excel.Application")


def _check_com(prog_id: str) -> bool:
    if sys.platform != "win32":
        return False
    try:
        import pythoncom
        import win32com.client

        pythoncom.CoInitialize()
        app = None
        try:
            app = win32com.client.DispatchEx(prog_id)
            return True
        except Exception:
            return False
        finally:
            if app is not None:
                app.Quit()
            pythoncom.CoUninitialize()
    except Exception:
        return False


def find_poppler_tools(config: Config) -> dict[str, str | None]:
    search_dirs: list[Path] = []
    if config.poppler_path:
        search_dirs.append(Path(config.poppler_path).expanduser())
    tools: dict[str, str | None] = {}
    for tool in POPPLER_TOOLS:
        found = None
        for directory in search_dirs:
            candidate = directory / f"{tool}.exe"
            if candidate.exists():
                found = str(candidate.resolve().absolute())
                break
        if found is None:
            found = shutil.which(tool)
        tools[tool] = found
    return tools


def doctor_report(config: Config, *, office_smoke: bool = False) -> dict[str, object]:
    packages = {
        package: {"module": module, "available": check_import(module)}
        for package, module in PYTHON_PACKAGES.items()
    }
    word_available = check_word_com()
    excel_available = check_excel_com()
    poppler = find_poppler_tools(config)
    report: dict[str, object] = {
        "python": {
            "executable": sys.executable,
            "version": sys.version,
        },
        "packages": packages,
        "office": {
            "word_com_available": word_available,
            "excel_com_available": excel_available,
        },
        "poppler": {
            "tools": poppler,
            "available": all(poppler.values()),
            "configured_path": config.poppler_path,
        },
        "core": {
            "backend": core_bridge.backend(),
            "rust_available": core_bridge.rust_available(),
            "version": core_bridge.version(),
        },
        "paths": {
            "cwd": str(Path.cwd().resolve().absolute()),
            "outputs_dir": str(config.outputs_path),
            "logs_dir": str(config.logs_path),
            "work_dir": str(config.work_path),
            "diagnostics_dir": str(config.diagnostics_path),
        },
        "windows": {
            "long_path_risk": sys.platform == "win32",
        },
    }
    if office_smoke:
        report["office_smoke"] = {
            "word_dispatch": word_available,
            "excel_dispatch": excel_available,
            "interactive_dialogs_checked": False,
        }
    return report
