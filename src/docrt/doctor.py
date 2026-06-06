from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

from docrt import core_bridge
from docrt.config import Config
from docrt.office_com import check_excel_com as _check_excel_com
from docrt.office_com import check_word_com as _check_word_com

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
    return _check_word_com()


def check_excel_com() -> bool:
    return _check_excel_com()


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


def doctor_report(
    config: Config, *, office_smoke: bool = False, agent: bool = False
) -> dict[str, object]:
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
        "uv": {
            "available": shutil.which("uv") is not None,
            "path": shutil.which("uv"),
            "required_entrypoint": "uv run docrt",
            "auto_bootstrap_command": "winget install --id astral-sh.uv -e",
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
    if agent:
        report["agent"] = agent_report(config, report)
    return report


def agent_report(config: Config, base_report: dict[str, object] | None = None) -> dict[str, object]:
    report = base_report or doctor_report(config)
    packages = report["packages"]
    assert isinstance(packages, dict)
    optional_package_names = {"pytest"}
    required_packages = {
        name: bool(value.get("available")) if isinstance(value, dict) else False
        for name, value in packages.items()
        if name not in optional_package_names
    }
    optional_packages = {
        name: bool(value.get("available")) if isinstance(value, dict) else False
        for name, value in packages.items()
        if name in optional_package_names
    }
    writable_paths = {
        "outputs": _is_writable(config.outputs_path),
        "logs": _is_writable(config.logs_path),
        "work": _is_writable(config.work_path),
        "cache": _is_writable(config.work_path / "cache"),
        "diagnostics": _is_writable(config.diagnostics_path),
    }
    poppler = report["poppler"]
    office = report["office"]
    core = report["core"]
    uv = report["uv"]
    assert isinstance(poppler, dict)
    assert isinstance(office, dict)
    assert isinstance(core, dict)
    assert isinstance(uv, dict)
    uv_required_ok = bool(uv.get("available"))
    word_required_ok = bool(office.get("word_com_available"))
    excel_required_ok = bool(office.get("excel_com_available"))
    required_ok = (
        all(required_packages.values())
        and all(writable_paths.values())
        and uv_required_ok
        and word_required_ok
        and excel_required_ok
    )
    return {
        "ready": required_ok,
        "project_root": str(Path.cwd().resolve().absolute()),
        "in_docrt_project": (Path.cwd() / "pyproject.toml").exists()
        and (Path.cwd() / "src" / "docrt").exists(),
        "required": {
            "packages": required_packages,
            "paths_writable": writable_paths,
            "cli_json_contract": True,
            "uv_entrypoint": uv_required_ok,
            "word_com_available": word_required_ok,
            "excel_com_available": excel_required_ok,
        },
        "optional": {
            "packages": optional_packages,
            "word_com_available": bool(office.get("word_com_available")),
            "excel_com_available": bool(office.get("excel_com_available")),
            "poppler_available": bool(poppler.get("available")),
            "rust_core_available": bool(core.get("rust_available")),
        },
        "recommended_doctor_command": "uv run docrt doctor --agent --office-smoke",
    }


def _is_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".docrt-write-test"
        probe.write_text("", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return os.access(path, os.W_OK)
    except OSError:
        return False
