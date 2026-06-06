from __future__ import annotations

import pytest

from docrt.runtime_env import confirmed_mainline_runtime


@pytest.fixture(autouse=True)
def _unit_tests_run_after_runtime_preflight():
    with confirmed_mainline_runtime():
        yield
