from __future__ import annotations

import subprocess
from pathlib import Path

from docrt.config import Config
from docrt.doctor import find_poppler_tools
from docrt.models import ErrorCode
from docrt.paths import ValidationError


def pdfinfo(path: Path, config: Config) -> dict[str, object]:
    tools = find_poppler_tools(config)
    executable = tools.get("pdfinfo")
    if not executable:
        raise ValidationError(ErrorCode.POPPLER_UNAVAILABLE, "pdfinfo was not found")
    completed = subprocess.run(
        [executable, str(path)],
        shell=False,
        check=False,
        capture_output=True,
        text=True,
        timeout=config.poppler_timeout_seconds,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "executable": executable,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
