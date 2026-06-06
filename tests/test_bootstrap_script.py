from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_bootstrap_uv_script_reports_existing_uv() -> None:
    script = Path("scripts/bootstrap-uv.ps1")

    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-NoInstall",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode in {0, 2}
    payload = json.loads(completed.stdout)
    assert "uv_available" in payload
    if completed.returncode == 0:
        assert payload["ok"] is True
        assert payload["uv_available"] is True
    else:
        assert payload["ok"] is False
        assert payload["error_code"] == "UV_UNAVAILABLE"
