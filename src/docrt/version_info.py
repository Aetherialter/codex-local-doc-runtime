from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from docrt import core_bridge

PACKAGE_NAME = "codex-local-doc-runtime"
RESULT_SCHEMA_VERSION = "1.0"
ERROR_SCHEMA_VERSION = "1.0"


def version_report() -> dict[str, object]:
    return {
        "package": PACKAGE_NAME,
        "version": package_version(),
        "stability": "stable",
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "error_schema_version": ERROR_SCHEMA_VERSION,
        "core": {
            "backend": core_bridge.backend(),
            "rust_available": core_bridge.rust_available(),
            "version": core_bridge.version(),
        },
    }


def package_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "0+unknown"
