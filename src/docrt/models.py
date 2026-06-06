from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import IntEnum, StrEnum
from typing import Any


class ErrorCode(StrEnum):
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    UNSUPPORTED_LEGACY_FORMAT = "UNSUPPORTED_LEGACY_FORMAT"
    ENCRYPTED_FILE_UNSUPPORTED = "ENCRYPTED_FILE_UNSUPPORTED"
    OCR_UNSUPPORTED = "OCR_UNSUPPORTED"
    PDF_ORIGINAL_EDIT_UNSUPPORTED = "PDF_ORIGINAL_EDIT_UNSUPPORTED"
    INTERACTIVE_OFFICE_DIALOG_UNSUPPORTED = "INTERACTIVE_OFFICE_DIALOG_UNSUPPORTED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    FILE_LOCKED = "FILE_LOCKED"
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    WORD_COM_UNAVAILABLE = "WORD_COM_UNAVAILABLE"
    EXCEL_COM_UNAVAILABLE = "EXCEL_COM_UNAVAILABLE"
    WORD_CONVERSION_FAILED = "WORD_CONVERSION_FAILED"
    EXCEL_CONVERSION_FAILED = "EXCEL_CONVERSION_FAILED"
    OFFICE_TIMEOUT = "OFFICE_TIMEOUT"
    OFFICE_PROCESS_CLEANUP_FAILED = "OFFICE_PROCESS_CLEANUP_FAILED"
    PDF_OPEN_FAILED = "PDF_OPEN_FAILED"
    PDF_RENDER_FAILED = "PDF_RENDER_FAILED"
    DOCX_READ_FAILED = "DOCX_READ_FAILED"
    DOCX_WRITE_FAILED = "DOCX_WRITE_FAILED"
    XLSX_READ_FAILED = "XLSX_READ_FAILED"
    XLSX_WRITE_FAILED = "XLSX_WRITE_FAILED"
    POPPLER_UNAVAILABLE = "POPPLER_UNAVAILABLE"
    PATH_VALIDATION_FAILED = "PATH_VALIDATION_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ExitCode(IntEnum):
    SUCCESS = 0
    OPERATION_FAILED = 1
    INVALID_ARGUMENT = 2
    UNSUPPORTED_FORMAT = 3
    FILE_NOT_FOUND = 4
    DEPENDENCY_MISSING = 5
    OFFICE_UNAVAILABLE = 6
    TIMEOUT = 7
    PERMISSION_DENIED = 8
    INTERNAL_ERROR = 9


@dataclass(slots=True)
class Result:
    ok: bool
    operation: str
    input_path: str | None
    output_path: str | None
    backend: str | None
    run_id: str
    started_at: str
    ended_at: str
    duration_ms: int
    error_code: str | None = None
    error_message: str | None = None
    exception_type: str | None = None
    traceback: str | None = None
    recovery_actions: list[str] = field(default_factory=list)
    diagnostic_report_path: str | None = None
    log_path: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ERROR_EXIT_MAP: dict[str, ExitCode] = {
    ErrorCode.UNSUPPORTED_FORMAT.value: ExitCode.UNSUPPORTED_FORMAT,
    ErrorCode.UNSUPPORTED_LEGACY_FORMAT.value: ExitCode.UNSUPPORTED_FORMAT,
    ErrorCode.ENCRYPTED_FILE_UNSUPPORTED.value: ExitCode.UNSUPPORTED_FORMAT,
    ErrorCode.OCR_UNSUPPORTED.value: ExitCode.UNSUPPORTED_FORMAT,
    ErrorCode.PDF_ORIGINAL_EDIT_UNSUPPORTED.value: ExitCode.UNSUPPORTED_FORMAT,
    ErrorCode.INTERACTIVE_OFFICE_DIALOG_UNSUPPORTED.value: ExitCode.OFFICE_UNAVAILABLE,
    ErrorCode.FILE_NOT_FOUND.value: ExitCode.FILE_NOT_FOUND,
    ErrorCode.DEPENDENCY_MISSING.value: ExitCode.DEPENDENCY_MISSING,
    ErrorCode.POPPLER_UNAVAILABLE.value: ExitCode.DEPENDENCY_MISSING,
    ErrorCode.WORD_COM_UNAVAILABLE.value: ExitCode.OFFICE_UNAVAILABLE,
    ErrorCode.EXCEL_COM_UNAVAILABLE.value: ExitCode.OFFICE_UNAVAILABLE,
    ErrorCode.OFFICE_TIMEOUT.value: ExitCode.TIMEOUT,
    ErrorCode.PERMISSION_DENIED.value: ExitCode.PERMISSION_DENIED,
    ErrorCode.FILE_LOCKED.value: ExitCode.PERMISSION_DENIED,
}


def exit_code_for_result(result: Result) -> ExitCode:
    if result.ok:
        return ExitCode.SUCCESS
    if result.error_code is None:
        return ExitCode.OPERATION_FAILED
    return ERROR_EXIT_MAP.get(result.error_code, ExitCode.OPERATION_FAILED)
