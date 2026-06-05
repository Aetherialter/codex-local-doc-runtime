from __future__ import annotations

from docrt.models import ErrorCode

RECOVERY_ACTIONS: dict[str, list[str]] = {
    ErrorCode.FILE_NOT_FOUND.value: [
        "Confirm the input path is absolute or relative to the current working directory.",
        "Check that the file exists and was not moved or deleted.",
    ],
    ErrorCode.UNSUPPORTED_FORMAT.value: [
        "Use a supported .docx, .pdf, or .xlsx file.",
        "Convert legacy .doc or .xls files before running docrt.",
    ],
    ErrorCode.PATH_VALIDATION_FAILED.value: [
        "Shorten the file path or move the project closer to the drive root.",
        "Avoid generated paths longer than 260 characters on Windows.",
    ],
    ErrorCode.PERMISSION_DENIED.value: [
        "Run PowerShell with access to the target directory.",
        "Check antivirus, folder permissions, and read-only attributes.",
    ],
    ErrorCode.FILE_LOCKED.value: [
        "Close Word, Excel, PDF viewers, or sync tools holding the file.",
        "Write outputs to a new filename and retry.",
    ],
    ErrorCode.DEPENDENCY_MISSING.value: [
        "Run uv sync --dev from the repository root.",
        "Run uv run docrt doctor to confirm required Python packages.",
    ],
    ErrorCode.WORD_COM_UNAVAILABLE.value: [
        "Install Microsoft Word desktop edition.",
        "Close existing Word dialogs and rerun uv run docrt doctor.",
    ],
    ErrorCode.EXCEL_COM_UNAVAILABLE.value: [
        "Install Microsoft Excel desktop edition.",
        "Close existing Excel dialogs and rerun uv run docrt doctor.",
    ],
    ErrorCode.POPPLER_UNAVAILABLE.value: [
        "Install Poppler tools or provide --poppler-path.",
        "Confirm pdfinfo, pdftoppm, and pdftocairo are visible to PowerShell.",
    ],
    ErrorCode.OFFICE_TIMEOUT.value: [
        "Increase --timeout for large documents.",
        "Close Office dialogs and retry with a simpler output path.",
    ],
    ErrorCode.WORD_CONVERSION_FAILED.value: [
        "Open the DOCX manually in Word to check repair prompts.",
        "Retry with --timeout increased after closing Word.",
    ],
    ErrorCode.EXCEL_CONVERSION_FAILED.value: [
        "Open the XLSX manually in Excel to check repair prompts.",
        "Retry with --timeout increased after closing Excel.",
    ],
    ErrorCode.VALIDATION_FAILED.value: [
        "Validate the JSON patch or task manifest before execution.",
        "Check expected_text, expected_value, file paths, and operation names.",
    ],
    ErrorCode.UNKNOWN_ERROR.value: [
        "Open the diagnostic_report_path JSON for traceback details.",
        "Rerun the same command after uv run docrt doctor.",
    ],
}


def recovery_actions(error_code: str | None) -> list[str]:
    if error_code is None:
        return []
    return RECOVERY_ACTIONS.get(error_code, RECOVERY_ACTIONS[ErrorCode.UNKNOWN_ERROR.value])
