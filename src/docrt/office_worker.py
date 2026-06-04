from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["word", "excel"])
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--result-json", required=True)
    args = parser.parse_args()

    result_path = Path(args.result_json)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if args.kind == "word":
            data = _convert_word(Path(args.input), Path(args.output))
        else:
            data = _convert_excel(Path(args.input), Path(args.output))
        payload = {"ok": True, "data": data}
        result_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return 0
    except Exception as exc:
        payload = {
            "ok": False,
            "error_message": str(exc),
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        }
        result_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return 1


def _convert_word(input_path: Path, output_path: Path) -> dict[str, object]:
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    app = None
    document = None
    try:
        app = win32com.client.DispatchEx("Word.Application")
        app.Visible = False
        app.DisplayAlerts = 0
        document = app.Documents.Open(str(input_path), ReadOnly=True)
        document.ExportAsFixedFormat(str(output_path), 17)
        return {"input_path": str(input_path), "output_path": str(output_path)}
    finally:
        if document is not None:
            document.Close(False)
        if app is not None:
            app.Quit()
        pythoncom.CoUninitialize()


def _convert_excel(input_path: Path, output_path: Path) -> dict[str, object]:
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    app = None
    workbook = None
    try:
        app = win32com.client.DispatchEx("Excel.Application")
        app.Visible = False
        app.DisplayAlerts = False
        workbook = app.Workbooks.Open(str(input_path), ReadOnly=True)
        workbook.ExportAsFixedFormat(0, str(output_path))
        return {"input_path": str(input_path), "output_path": str(output_path)}
    finally:
        if workbook is not None:
            workbook.Close(False)
        if app is not None:
            app.Quit()
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    raise SystemExit(main())
