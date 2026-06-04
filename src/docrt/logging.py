from __future__ import annotations

from pathlib import Path
from typing import Any

from docrt.jsonutil import dump_file, dumps


class JsonlLogger:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: dict[str, Any]) -> None:
        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(dumps(event))
            file.write("\n")


def write_diagnostic(path: Path, payload: dict[str, Any]) -> Path:
    dump_file(path, payload, pretty=True)
    return path
