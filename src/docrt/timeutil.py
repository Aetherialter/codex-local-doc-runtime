from __future__ import annotations

from datetime import UTC, datetime
from secrets import token_hex
from time import perf_counter


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def make_run_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{token_hex(3)}"


class Timer:
    def __init__(self) -> None:
        self.started_at = utc_now_iso()
        self._start = perf_counter()

    def finish(self) -> tuple[str, int]:
        ended_at = utc_now_iso()
        duration_ms = int((perf_counter() - self._start) * 1000)
        return ended_at, duration_ms
