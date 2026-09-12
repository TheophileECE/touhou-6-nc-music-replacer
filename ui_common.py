from __future__ import annotations

import os
import tkinter as tk

APP_TITLE = "Touhou 6 NC Music Replacer"
AUDIO_TYPES = {".mp3", ".wav", ".flac", ".ogg", ".opus", ".m4a", ".aac", ".wma"}

BG = "#f7f4f6"
CARD = "#ffffff"
TEXT = "#2b2528"
MUTED = "#6e6268"
ACCENT = "#c84367"
ACCENT_HOVER = "#ae3457"
ACCENT_SOFT = "#fae9ef"
SUCCESS = "#2f7d5c"
SUCCESS_SOFT = "#e8f4ee"
BORDER = "#e4dce0"
WARNING = "#9c641c"
WARNING_SOFT = "#fff5df"
ERROR = "#a24343"
DROP_BG = "#fbf8f9"


def enable_dpi_awareness() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def center_window(window: tk.Toplevel | tk.Tk, width: int, height: int) -> None:
    window.update_idletasks()
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()
    x = max(0, (sw - width) // 2)
    y = max(0, (sh - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
