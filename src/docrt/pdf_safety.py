from __future__ import annotations

from typing import Any

from docrt.models import ErrorCode
from docrt.paths import ValidationError


def ensure_pdf_not_encrypted(document: Any) -> None:
    if bool(getattr(document, "is_encrypted", False)) or bool(
        getattr(document, "needs_pass", False)
    ):
        raise ValidationError(
            ErrorCode.ENCRYPTED_FILE_UNSUPPORTED,
            "Encrypted PDF files are not supported in v1.1",
            context={
                "document_type": "pdf",
                "needs_pass": bool(getattr(document, "needs_pass", False)),
            },
        )


def pdf_text_layer_warnings(total_text_chars: int) -> list[str]:
    if total_text_chars:
        return []
    return [
        "PDF has no text layer; OCR is not supported in v1.1.",
        "Use an external OCR tool before running docrt text extraction.",
    ]
