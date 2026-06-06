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
    ErrorCode.UNSUPPORTED_LEGACY_FORMAT.value: [
        "Convert .doc to .docx or .xls to .xlsx before running docrt.",
        "Use Microsoft Office or another trusted converter outside docrt.",
    ],
    ErrorCode.CORRUPT_DOCUMENT.value: [
        "Open the document in its native application and save a repaired copy.",
        "Retry with a known-good .docx, .pdf, or .xlsx file.",
    ],
    ErrorCode.ENCRYPTED_FILE_UNSUPPORTED.value: [
        "Create an unencrypted copy of the document before running docrt.",
        "Do not pass passwords through logs, task manifests, or patch files.",
    ],
    ErrorCode.OCR_UNSUPPORTED.value: [
        "Run an external OCR tool first, then pass the text-layer PDF to docrt.",
        "Use inspect-pdf or read-pdf to confirm has_text_layer before text extraction.",
    ],
    ErrorCode.PDF_ORIGINAL_EDIT_UNSUPPORTED.value: [
        "Use annotate-pdf for additive comments or marks.",
        "Use a dedicated PDF editor for original-content editing.",
    ],
    ErrorCode.INTERACTIVE_OFFICE_DIALOG_UNSUPPORTED.value: [
        (
            "Open Word or Excel manually and clear first-run prompts, repair prompts, "
            "or macro warnings."
        ),
        "Rerun uv run docrt doctor --agent --office-smoke after closing Office dialogs.",
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
    ErrorCode.UV_UNAVAILABLE.value: [
        "Install uv with winget install --id astral-sh.uv -e.",
        "Open a new PowerShell session, then rerun uv run docrt doctor --agent.",
    ],
    ErrorCode.UV_BOOTSTRAP_FAILED.value: [
        "Install uv manually with winget install --id astral-sh.uv -e.",
        "If winget is unavailable, install uv from the official Astral release channel.",
    ],
    ErrorCode.OFFICE_COM_REQUIRED.value: [
        "Install Microsoft Word and Microsoft Excel desktop editions.",
        "Rerun uv run docrt doctor --agent --office-smoke.",
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
