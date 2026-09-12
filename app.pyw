from __future__ import annotations

import tkinter as tk
from pathlib import Path

from runtime_bootstrap import ensure_runtime

ensure_runtime()

from tkinterdnd2 import TkinterDnD  # noqa: E402
from ui_actions import ActionsMixin  # noqa: E402
from ui_common import APP_TITLE, BG, enable_dpi_awareness, center_window  # noqa: E402
from ui_layout import LayoutMixin  # noqa: E402


class FriendlyApp(LayoutMixin, ActionsMixin, TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.configure(bg=BG)
        self.minsize(740, 560)
        center_window(self, 960, 740)

        self.game_root = tk.StringVar()
        self.source_file = tk.StringVar()
        self.music_bank = tk.StringVar(value="bgm")
        self.track_choice = tk.StringVar()
        self.loop_mode = tk.StringVar(value="whole")
        self.loop_start = tk.StringVar(value="0.000")
        self.status_text = tk.StringVar(value="Start by choosing your Touhou 6 New Classic folder.")
        self.status_kind = "neutral"
        self.track_paths: dict[str, Path] = {}
        self.bank_buttons: dict[str, tk.Button] = {}
        self.drop_parts: dict[tk.Frame, dict[str, object]] = {}
        self.current_loop = None
        self.busy = False
        self._compact_layout = False

        self._setup_styles()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Configure>", self._on_resize, add="+")


if __name__ == "__main__":
    enable_dpi_awareness()
    FriendlyApp().mainloop()
