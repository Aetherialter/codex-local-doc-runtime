from __future__ import annotations

import sys


def check_word_com() -> bool:
    return check_com_dispatch("Word.Application")


def check_excel_com() -> bool:
    return check_com_dispatch("Excel.Application")


def check_com_dispatch(prog_id: str) -> bool:
    if sys.platform != "win32":
        return False
    try:
        import pythoncom
        import win32com.client

        pythoncom.CoInitialize()
        app = None
        try:
            app = win32com.client.DispatchEx(prog_id)
            return True
        except Exception:
            return False
        finally:
            if app is not None:
                app.Quit()
            pythoncom.CoUninitialize()
    except Exception:
        return False
