"""
桌面文件对话框能力。
"""

import ctypes
import platform
from ctypes import wintypes


OFN_FILEMUSTEXIST = 0x00001000
OFN_PATHMUSTEXIST = 0x00000800
MAX_PATH = 260


class OPENFILENAMEW(ctypes.Structure):
    _fields_ = [
        ("lStructSize", wintypes.DWORD),
        ("hwndOwner", wintypes.HWND),
        ("hInstance", wintypes.HINSTANCE),
        ("lpstrFilter", wintypes.LPCWSTR),
        ("lpstrCustomFilter", wintypes.LPWSTR),
        ("nMaxCustFilter", wintypes.DWORD),
        ("nFilterIndex", wintypes.DWORD),
        ("lpstrFile", wintypes.LPWSTR),
        ("nMaxFile", wintypes.DWORD),
        ("lpstrFileTitle", wintypes.LPWSTR),
        ("nMaxFileTitle", wintypes.DWORD),
        ("lpstrInitialDir", wintypes.LPCWSTR),
        ("lpstrTitle", wintypes.LPCWSTR),
        ("Flags", wintypes.DWORD),
        ("nFileOffset", wintypes.WORD),
        ("nFileExtension", wintypes.WORD),
        ("lpstrDefExt", wintypes.LPCWSTR),
        ("lCustData", wintypes.LPARAM),
        ("lpfnHook", wintypes.LPVOID),
        ("lpTemplateName", wintypes.LPCWSTR),
        ("pvReserved", wintypes.LPVOID),
        ("dwReserved", wintypes.DWORD),
        ("FlagsEx", wintypes.DWORD),
    ]


def _show_file_dialog_windows_native() -> str:
    """
    使用 Windows 原生 API 打开文件选择对话框。
    """

    buffer = ctypes.create_unicode_buffer(MAX_PATH)
    ofn = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    ofn.lpstrFile = ctypes.cast(buffer, wintypes.LPWSTR)
    ofn.nMaxFile = MAX_PATH
    ofn.lpstrFilter = "All Files\0*.*\0\0"
    ofn.lpstrTitle = "选择文件"
    ofn.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST

    comdlg32 = ctypes.windll.comdlg32
    comdlg32.GetOpenFileNameW.argtypes = [ctypes.POINTER(OPENFILENAMEW)]
    comdlg32.GetOpenFileNameW.restype = wintypes.BOOL

    success = comdlg32.GetOpenFileNameW(ctypes.byref(ofn))
    return buffer.value if success else ""


def show_file_dialog() -> str:
    """
    弹出文件对话框。
    优先使用 tkinter，若不可用则在 Windows 上回退到原生对话框。
    """

    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        file_path = filedialog.askopenfilename()
        root.destroy()
        return file_path
    except ModuleNotFoundError:
        if platform.system() == "Windows":
            return _show_file_dialog_windows_native()
        raise RuntimeError("tkinter is not available on this platform")
