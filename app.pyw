from __future__ import annotations

import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

BASE = Path(__file__).resolve().parent
VENV = BASE / ".venv"
REQUIREMENTS = BASE / "requirements.txt"
READY = VENV / ".ready"


def _hidden_flags() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


def _venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _venv_pythonw() -> Path:
    if os.name == "nt":
        candidate = VENV / "Scripts/pythonw.exe"
        return candidate if candidate.exists() else _venv_python()
    return _venv_python()


def _running_in_private_env() -> bool:
    try:
        return Path(sys.executable).resolve().is_relative_to(VENV.resolve())
    except AttributeError:
        try:
            Path(sys.executable).resolve().relative_to(VENV.resolve())
            return True
        except ValueError:
            return False


def _launch_private_app() -> None:
    subprocess.Popen(
        [str(_venv_pythonw()), str(Path(__file__).resolve())],
        cwd=str(BASE),
        creationflags=_hidden_flags(),
    )


class _FirstRunSetup(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Touhou 6 NC Music Replacer")
        self.configure(bg="#f7f4f6")
        self.resizable(False, False)
        self.geometry("520x260")

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 520) // 2
        y = (self.winfo_screenheight() - 260) // 2
        self.geometry(f"520x260+{max(0, x)}+{max(0, y)}")

        card = tk.Frame(self, bg="white", highlightbackground="#e4dce0", highlightthickness=1)
        card.pack(fill="both", expand=True, padx=22, pady=22)
        tk.Label(card, text="First-time setup", bg="white", fg="#2b2528", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=24, pady=(24, 6))
        tk.Label(
            card,
            text="Preparing drag-and-drop and the audio converter. Everything stays inside this tool's folder.",
            bg="white",
            fg="#6e6268",
            justify="left",
            wraplength=420,
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=24)
        self.status = tk.StringVar(value="Preparing the app…")
        tk.Label(card, textvariable=self.status, bg="white", fg="#c84367", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=24, pady=(18, 7))
        self.progress = ttk.Progressbar(card, mode="indeterminate")
        self.progress.pack(fill="x", padx=24, pady=(0, 24))
        self.progress.start(12)
        threading.Thread(target=self._worker, daemon=True).start()

    def _run(self, command: list[str], message: str) -> None:
        self.after(0, self.status.set, message)
        result = subprocess.run(
            command,
            cwd=str(BASE),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=_hidden_flags(),
            check=False,
        )
        if result.returncode:
            tail = "\n".join((result.stdout or "").splitlines()[-12:])
            raise RuntimeError(tail or f"Setup failed with exit code {result.returncode}.")

    def _worker(self) -> None:
        try:
            if not _venv_python().is_file():
                self._run([sys.executable, "-m", "venv", str(VENV)], "Creating a private environment…")
            self._run(
                [str(_venv_python()), "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", str(REQUIREMENTS)],
                "Installing the two small runtime dependencies…",
            )
            READY.write_text("ready\n", encoding="utf-8")
            self.after(0, self._finish)
        except Exception as exc:
            self.after(0, self._fail, exc)

    def _finish(self) -> None:
        self.progress.stop()
        self.status.set("Ready! Opening the music replacer…")
        try:
            _launch_private_app()
            self.after(250, self.destroy)
        except Exception as exc:
            self._fail(exc)

    def _fail(self, exc: Exception) -> None:
        self.progress.stop()
        messagebox.showerror(
            "Setup could not finish",
            "The app could not prepare its local runtime.\n\n"
            f"Details:\n{exc}\n\n"
            "Check that Python 3 has internet access, then launch the app again.",
            parent=self,
        )
        self.destroy()


def _ensure_private_runtime() -> None:
    if _running_in_private_env():
        return
    if READY.is_file() and _venv_python().is_file():
        _launch_private_app()
        raise SystemExit
    _FirstRunSetup().mainloop()
    raise SystemExit


_ensure_private_runtime()

from tkinterdnd2 import DND_FILES, TkinterDnD  # noqa: E402
from core import (  # noqa: E402
    POS_RATE,
    TRACK_TITLES,
    PosStore,
    ToolError,
    convert,
    parse_track_number,
    samples48_to_pos_samples,
)

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


def _enable_dpi_awareness() -> None:
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


def _center_window(window: tk.Toplevel | tk.Tk, width: int, height: int) -> None:
    window.update_idletasks()
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()
    x = max(0, (sw - width) // 2)
    y = max(0, (sh - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def _open_in_explorer(path: Path) -> None:
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


class TutorialDialog(tk.Toplevel):
    PAGES = [
        (
            "Welcome",
            "This tool replaces Touhou 6 New Classic music without leaving the old song's loop points behind. "
            "You only need your game folder and a replacement song.",
        ),
        (
            "1. Choose the game",
            "Drag the folder that contains th06nc.exe onto the first box, or click Browse. "
            "The tool checks data/bgm and th06MD.dat before it lets you continue.",
        ),
        (
            "2. Pick a slot and a song",
            "Choose which Touhou track you want to replace, then drag in an MP3, WAV, FLAC, OGG, Opus, M4A, AAC or WMA file. "
            "The song is automatically converted to the Nintendo Opus format used by the game.",
        ),
        (
            "3. Looping made simple",
            "For most custom music, leave 'Loop the whole song' selected. The tool writes a new loop end matching your replacement song. "
            "Advanced users can choose a custom loop start so an intro plays only once.",
        ),
        (
            "4. Safe replacement",
            "Click Replace Music. The first time a slot is changed, the original Opus and loop metadata are backed up as .original.bak. "
            "Use Restore Original later if you want that slot back exactly as it was.",
        ),
    ]

    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.title("Quick tutorial")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.index = 0

        body = tk.Frame(self, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        body.pack(fill="both", expand=True, padx=24, pady=24)

        self.step = tk.Label(body, bg=CARD, fg=ACCENT, font=("Segoe UI", 10, "bold"))
        self.step.pack(anchor="w", padx=26, pady=(24, 4))
        self.heading = tk.Label(body, bg=CARD, fg=TEXT, font=("Segoe UI", 20, "bold"))
        self.heading.pack(anchor="w", padx=26)
        self.copy = tk.Label(
            body,
            bg=CARD,
            fg=MUTED,
            justify="left",
            wraplength=550,
            font=("Segoe UI", 11),
        )
        self.copy.pack(anchor="w", fill="x", padx=26, pady=(14, 24))

        nav = tk.Frame(body, bg=CARD)
        nav.pack(fill="x", padx=26, pady=(0, 24))
        self.back_btn = tk.Button(nav, text="Back", command=self.back, font=("Segoe UI", 10, "bold"), relief="flat", padx=18, pady=9)
        self.back_btn.pack(side="left")
        self.next_btn = tk.Button(
            nav,
            text="Next",
            command=self.next,
            bg=ACCENT,
            activebackground=ACCENT_HOVER,
            fg="white",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=24,
            pady=9,
            cursor="hand2",
        )
        self.next_btn.pack(side="right")

        self.show_page()
        _center_window(self, 650, 360)

    def show_page(self) -> None:
        title, copy = self.PAGES[self.index]
        self.step.configure(text=f"STEP {self.index + 1} OF {len(self.PAGES)}")
        self.heading.configure(text=title)
        self.copy.configure(text=copy)
        self.back_btn.configure(state="normal" if self.index else "disabled")
        self.next_btn.configure(text="Got it" if self.index == len(self.PAGES) - 1 else "Next")

    def back(self) -> None:
        if self.index > 0:
            self.index -= 1
            self.show_page()

    def next(self) -> None:
        if self.index >= len(self.PAGES) - 1:
            self.destroy()
            return
        self.index += 1
        self.show_page()


class FriendlyApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.configure(bg=BG)
        self.minsize(900, 700)
        _center_window(self, 1080, 820)

        self.game_root = tk.StringVar()
        self.source_file = tk.StringVar()
        self.track_choice = tk.StringVar()
        self.loop_mode = tk.StringVar(value="whole")
        self.loop_start = tk.StringVar(value="0.000")
        self.status_text = tk.StringVar(value="Start by choosing your Touhou 6 New Classic folder.")
        self.status_kind = "neutral"
        self.track_paths: dict[str, Path] = {}
        self.current_loop = None
        self.busy = False

        self._setup_styles()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Friendly.TCombobox",
            font=("Segoe UI", 12),
            padding=10,
            fieldbackground="white",
            background="white",
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
        )
        style.map("Friendly.TCombobox", fieldbackground=[("readonly", "white")])
        style.configure("Friendly.Horizontal.TProgressbar", troughcolor="#efe8eb", background=ACCENT, thickness=11)

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.content = tk.Frame(canvas, bg=BG)
        window_id = canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        page = tk.Frame(self.content, bg=BG)
        page.pack(fill="both", expand=True, padx=34, pady=26)

        header = tk.Frame(page, bg=BG)
        header.pack(fill="x", pady=(0, 18))
        text_col = tk.Frame(header, bg=BG)
        text_col.pack(side="left", fill="x", expand=True)
        tk.Label(text_col, text="Touhou 6 NC Music Replacer", bg=BG, fg=TEXT, font=("Segoe UI", 25, "bold")).pack(anchor="w")
        tk.Label(
            text_col,
            text="Replace a song, fix its loop automatically, and keep a safe backup of the original.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 11),
        ).pack(anchor="w", pady=(4, 0))
        self._button(header, "How does this work?", lambda: TutorialDialog(self), secondary=True).pack(side="right", padx=(16, 0))

        intro = tk.Frame(page, bg=ACCENT_SOFT, highlightbackground="#efcad6", highlightthickness=1)
        intro.pack(fill="x", pady=(0, 18))
        tk.Label(intro, text="No technical knowledge needed", bg=ACCENT_SOFT, fg=ACCENT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=20, pady=(14, 3))
        tk.Label(
            intro,
            text="The game stores the audio and its loop instructions separately. This tool updates both together so custom songs do not jump or loop at the old track's timing.",
            bg=ACCENT_SOFT,
            fg=TEXT,
            justify="left",
            wraplength=930,
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=20, pady=(0, 14))

        row = tk.Frame(page, bg=BG)
        row.pack(fill="x")
        row.grid_columnconfigure(0, weight=1, uniform="top")
        row.grid_columnconfigure(1, weight=1, uniform="top")

        game_card = self._card(row, "1", "Choose your game folder", "Drop the folder containing th06nc.exe here, or browse for it.")
        game_card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        self.game_drop = self._drop_zone(game_card, "Drop Touhou 6 NC folder here", "or drop th06nc.exe")
        self.game_drop.pack(fill="x", padx=20, pady=(4, 10))
        self._register_drop(self.game_drop, self._game_dropped)
        controls = tk.Frame(game_card, bg=CARD)
        controls.pack(fill="x", padx=20, pady=(0, 18))
        self._button(controls, "Browse game folder", self.browse_game).pack(side="left")
        self.game_state = tk.Label(controls, text="Not selected", bg=CARD, fg=MUTED, font=("Segoe UI", 10))
        self.game_state.pack(side="right", pady=10)

        track_card = self._card(row, "2", "Choose the music slot", "Pick the original Touhou track that your custom song will replace.")
        track_card.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        self.track_combo = ttk.Combobox(track_card, textvariable=self.track_choice, state="readonly", style="Friendly.TCombobox")
        self.track_combo.pack(fill="x", padx=20, pady=(8, 10))
        self.track_combo.bind("<<ComboboxSelected>>", lambda _: self.on_track_selected())
        self.track_info = tk.Label(
            track_card,
            text="Choose the game folder first.",
            bg=CARD,
            fg=MUTED,
            justify="left",
            wraplength=420,
            font=("Segoe UI", 10),
        )
        self.track_info.pack(anchor="w", fill="x", padx=20, pady=(0, 18))

        audio_card = self._card(page, "3", "Add your replacement song", "Drag in a common audio file. The tool handles the Nintendo Opus conversion for you.")
        audio_card.pack(fill="x", pady=(18, 0))
        self.audio_drop = self._drop_zone(audio_card, "Drop your song here", "MP3, WAV, FLAC, OGG, Opus, M4A, AAC or WMA")
        self.audio_drop.pack(fill="x", padx=20, pady=(4, 10))
        self._register_drop(self.audio_drop, self._audio_dropped)
        audio_controls = tk.Frame(audio_card, bg=CARD)
        audio_controls.pack(fill="x", padx=20, pady=(0, 18))
        self._button(audio_controls, "Browse for a song", self.browse_source).pack(side="left")
        self.audio_state = tk.Label(audio_controls, text="No song selected", bg=CARD, fg=MUTED, font=("Segoe UI", 10))
        self.audio_state.pack(side="right", pady=10)

        loop_card = self._card(page, "4", "Choose how it loops", "The simple option is best for most custom songs.")
        loop_card.pack(fill="x", pady=(18, 0))

        choices = tk.Frame(loop_card, bg=CARD)
        choices.pack(fill="x", padx=20, pady=(6, 8))
        self._radio(choices, "whole", "Loop the whole song", "The song restarts from 0:00 when it reaches the end.").pack(fill="x", pady=(0, 8))
        self._radio(choices, "custom", "Intro once, then loop from a custom point", "Useful when your track has an intro that should not repeat.").pack(fill="x")

        self.custom_loop_frame = tk.Frame(loop_card, bg="#fbf8f9")
        tk.Label(self.custom_loop_frame, text="Loop starts at", bg="#fbf8f9", fg=TEXT, font=("Segoe UI", 10, "bold")).pack(side="left", padx=(14, 8), pady=12)
        loop_entry = tk.Entry(
            self.custom_loop_frame,
            textvariable=self.loop_start,
            font=("Segoe UI", 12),
            width=11,
            relief="solid",
            bd=1,
            highlightthickness=0,
        )
        loop_entry.pack(side="left", pady=10)
        tk.Label(self.custom_loop_frame, text="seconds", bg="#fbf8f9", fg=MUTED, font=("Segoe UI", 10)).pack(side="left", padx=8)
        self._button(self.custom_loop_frame, "Use original loop start", self.use_original_start, secondary=True, compact=True).pack(side="right", padx=12, pady=8)
        self._update_loop_mode()
        self.loop_mode.trace_add("write", lambda *_: self._update_loop_mode())

        action_card = tk.Frame(page, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        action_card.pack(fill="x", pady=(18, 0))
        action_top = tk.Frame(action_card, bg=CARD)
        action_top.pack(fill="x", padx=20, pady=(18, 10))
        action_copy = tk.Frame(action_top, bg=CARD)
        action_copy.pack(side="left", fill="x", expand=True)
        tk.Label(action_copy, text="Ready when you are", bg=CARD, fg=TEXT, font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(action_copy, text="Original files are backed up automatically the first time you replace a slot.", bg=CARD, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 0))
        self.replace_button = self._button(action_top, "Replace Music", self.start_replace, big=True)
        self.replace_button.pack(side="right", padx=(20, 0))

        self.progress = ttk.Progressbar(action_card, mode="indeterminate", style="Friendly.Horizontal.TProgressbar")
        self.progress.pack(fill="x", padx=20, pady=(0, 10))

        self.status_box = tk.Frame(action_card, bg="#f5f1f3")
        self.status_box.pack(fill="x", padx=20, pady=(0, 18))
        self.status_label = tk.Label(
            self.status_box,
            textvariable=self.status_text,
            bg="#f5f1f3",
            fg=MUTED,
            justify="left",
            wraplength=820,
            font=("Segoe UI", 10),
        )
        self.status_label.pack(side="left", fill="x", expand=True, padx=14, pady=12)
        self.restore_button = self._button(self.status_box, "Restore Original", self.restore_selected, secondary=True, compact=True)
        self.restore_button.pack(side="right", padx=10, pady=7)


    def _card(self, parent: tk.Misc, number: str, title: str, subtitle: str) -> tk.Frame:
        card = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        heading = tk.Frame(card, bg=CARD)
        heading.pack(fill="x", padx=20, pady=(18, 6))
        badge = tk.Label(heading, text=number, bg=ACCENT, fg="white", font=("Segoe UI", 11, "bold"), width=3, height=1)
        badge.pack(side="left", padx=(0, 12))
        copy = tk.Frame(heading, bg=CARD)
        copy.pack(side="left", fill="x", expand=True)
        tk.Label(copy, text=title, bg=CARD, fg=TEXT, font=("Segoe UI", 15, "bold")).pack(anchor="w")
        tk.Label(copy, text=subtitle, bg=CARD, fg=MUTED, font=("Segoe UI", 9), wraplength=760, justify="left").pack(anchor="w", pady=(2, 0))
        return card

    def _drop_zone(self, parent: tk.Misc, title: str, subtitle: str) -> tk.Frame:
        zone = tk.Frame(parent, bg="#fbf8f9", highlightbackground="#d9cdd2", highlightthickness=2, cursor="hand2")
        icon = tk.Label(zone, text="+", bg="#fbf8f9", fg=ACCENT, font=("Segoe UI", 25, "bold"))
        icon.pack(pady=(12, 0))
        tk.Label(zone, text=title, bg="#fbf8f9", fg=TEXT, font=("Segoe UI", 12, "bold")).pack()
        tk.Label(zone, text=subtitle, bg="#fbf8f9", fg=MUTED, font=("Segoe UI", 9)).pack(pady=(2, 12))
        return zone

    def _button(
        self,
        parent: tk.Misc,
        text: str,
        command,
        *,
        secondary: bool = False,
        big: bool = False,
        compact: bool = False,
        link: bool = False,
    ) -> tk.Button:
        if link:
            return tk.Button(
                parent,
                text=text,
                command=command,
                bg=BG,
                activebackground=BG,
                fg=ACCENT,
                activeforeground=ACCENT_HOVER,
                font=("Segoe UI", 9, "underline"),
                relief="flat",
                bd=0,
                cursor="hand2",
            )
        if secondary:
            bg = "#f1ebee"
            fg = TEXT
            active = "#e7dfe3"
        else:
            bg = ACCENT
            fg = "white"
            active = ACCENT_HOVER
        if big:
            font = ("Segoe UI", 13, "bold")
            padx, pady = 34, 14
        elif compact:
            font = ("Segoe UI", 9, "bold")
            padx, pady = 14, 7
        else:
            font = ("Segoe UI", 10, "bold")
            padx, pady = 18, 10
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            activebackground=active,
            fg=fg,
            activeforeground=fg,
            font=font,
            relief="flat",
            bd=0,
            padx=padx,
            pady=pady,
            cursor="hand2",
        )

    def _radio(self, parent: tk.Misc, value: str, title: str, subtitle: str) -> tk.Frame:
        frame = tk.Frame(parent, bg="#fbf8f9", highlightthickness=1, highlightbackground=BORDER)
        radio = tk.Radiobutton(
            frame,
            variable=self.loop_mode,
            value=value,
            bg="#fbf8f9",
            activebackground="#fbf8f9",
            selectcolor="#fbf8f9",
            fg=ACCENT,
            font=("Segoe UI", 11, "bold"),
        )
        radio.pack(side="left", padx=(12, 8), pady=14)
        copy = tk.Frame(frame, bg="#fbf8f9")
        copy.pack(side="left", fill="x", expand=True, pady=10)
        tk.Label(copy, text=title, bg="#fbf8f9", fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(copy, text=subtitle, bg="#fbf8f9", fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))
        return frame

    def _register_drop(self, widget: tk.Misc, handler) -> None:
        for target in (widget, *widget.winfo_children()):
            try:
                target.drop_target_register(DND_FILES)  # type: ignore[attr-defined]
                target.dnd_bind("<<Drop>>", handler)  # type: ignore[attr-defined]
            except Exception:
                pass

    def _drop_paths(self, data: str) -> list[Path]:
        try:
            values = self.tk.splitlist(data)
        except tk.TclError:
            values = [data]
        return [Path(v.strip().strip("{}\"")) for v in values if v.strip()]

    def _game_dropped(self, event) -> str:
        paths = self._drop_paths(event.data)
        if not paths:
            return "break"
        path = paths[0]
        if path.is_file() and path.name.lower() == "th06nc.exe":
            path = path.parent
        if not path.is_dir():
            self._set_status("Please drop the game folder or th06nc.exe itself.", "warning")
            return "break"
        self.game_root.set(str(path))
        self.scan_game()
        return "break"

    def _audio_dropped(self, event) -> str:
        paths = self._drop_paths(event.data)
        if not paths:
            return "break"
        path = next((p for p in paths if p.is_file() and p.suffix.lower() in AUDIO_TYPES), None)
        if path is None:
            self._set_status("That does not look like a supported audio file.", "warning")
            return "break"
        self._set_audio(path)
        return "break"

    def browse_game(self) -> None:
        folder = filedialog.askdirectory(title="Choose the folder containing th06nc.exe")
        if folder:
            self.game_root.set(folder)
            self.scan_game()

    def browse_source(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose your replacement song",
            filetypes=[
                ("Audio files", "*.mp3 *.wav *.flac *.ogg *.opus *.m4a *.aac *.wma"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._set_audio(Path(path))

    def _set_audio(self, path: Path) -> None:
        self.source_file.set(str(path.resolve()))
        self.audio_state.configure(text=path.name, fg=SUCCESS)
        self._set_status(f"Song selected: {path.name}. Choose a track slot, then replace it when ready.", "success")

    def scan_game(self) -> None:
        try:
            game = Path(self.game_root.get()).expanduser().resolve()
            if not (game / "th06nc.exe").is_file():
                raise ToolError("This folder does not contain th06nc.exe.")
            bgm = game / "data" / "bgm"
            if not bgm.is_dir():
                raise ToolError("The game folder is missing data/bgm.")
            tracks = sorted(bgm.glob("th06_*.opus"))
            if not tracks:
                raise ToolError("No Touhou BGM files were found in data/bgm.")
            PosStore(game)

            self.track_paths.clear()
            labels: list[str] = []
            for path in tracks:
                number = parse_track_number(path.stem)
                title = TRACK_TITLES.get(number or -1, "")
                label = f"{path.stem}  —  {title}" if title else path.stem
                labels.append(label)
                self.track_paths[label] = path

            self.track_combo["values"] = labels
            self.track_choice.set(labels[0])
            self.game_state.configure(text=f"✓ Game detected · {len(tracks)} tracks", fg=SUCCESS)
            self.on_track_selected()
            self._set_status("Game detected successfully. Now choose the music slot you want to replace.", "success")
        except Exception as exc:
            self.track_paths.clear()
            self.track_combo["values"] = []
            self.track_choice.set("")
            self.current_loop = None
            self.game_state.configure(text="Game not detected", fg="#a24343")
            self.track_info.configure(text="Choose a valid game folder first.", fg=MUTED)
            self._set_status(str(exc), "warning")
            messagebox.showerror("Could not use this folder", str(exc), parent=self)

    def selected_track(self) -> Path:
        track = self.track_paths.get(self.track_choice.get())
        if not track:
            raise ToolError("Choose a music slot first.")
        return track

    def on_track_selected(self) -> None:
        try:
            game = Path(self.game_root.get()).expanduser().resolve()
            track = self.selected_track()
            info = PosStore(game).read(track.stem)
            self.current_loop = info
            self.track_info.configure(
                text=f"Current game loop: {info.start_seconds:.2f}s → {info.end_seconds:.2f}s\n"
                     "Your replacement gets new loop timing automatically.",
                fg=MUTED,
            )
        except Exception as exc:
            self.current_loop = None
            self.track_info.configure(text=f"Loop information could not be read: {exc}", fg="#a24343")

    def _update_loop_mode(self) -> None:
        if self.loop_mode.get() == "custom":
            self.custom_loop_frame.pack(fill="x", padx=20, pady=(2, 18))
        else:
            self.custom_loop_frame.pack_forget()

    def use_original_start(self) -> None:
        if not self.current_loop:
            messagebox.showinfo("No original loop loaded", "Choose a valid game and track first.", parent=self)
            return
        self.loop_start.set(f"{self.current_loop.start_seconds:.6f}")

    def _resolved_loop_start(self) -> float:
        if self.loop_mode.get() == "whole":
            return 0.0
        try:
            value = float(self.loop_start.get().strip())
        except ValueError as exc:
            raise ToolError("Enter the loop start as seconds, for example 12.500.") from exc
        if not math.isfinite(value) or value < 0:
            raise ToolError("Loop start must be 0 or a positive number of seconds.")
        return value

    def start_replace(self) -> None:
        if self.busy:
            return
        try:
            game = Path(self.game_root.get()).expanduser().resolve()
            track = self.selected_track()
            source = Path(self.source_file.get()).expanduser().resolve()
            if not source.is_file():
                raise ToolError("Choose a replacement song first.")
            loop_start = self._resolved_loop_start()
        except Exception as exc:
            messagebox.showerror("One more thing is needed", str(exc), parent=self)
            self._set_status(str(exc), "warning")
            return

        loop_copy = "the beginning of the song" if loop_start == 0 else f"{loop_start:.3f} seconds"
        if not messagebox.askyesno(
            "Replace this music?",
            f"Replace {track.name} with:\n\n{source.name}\n\n"
            f"Loop from: {loop_copy}\n\n"
            "The original track and loop metadata will be backed up automatically.",
            parent=self,
        ):
            return

        self.busy = True
        self.replace_button.configure(state="disabled")
        self.restore_button.configure(state="disabled")
        self.progress.start(12)
        self._set_status("Converting your song to the format used by Touhou 6 NC…", "neutral")
        threading.Thread(target=self._replace_worker, args=(game, track, source, loop_start), daemon=True).start()

    def _replace_worker(self, game: Path, track: Path, source: Path, start_seconds: float) -> None:
        try:
            store = PosStore(game)
            with tempfile.TemporaryDirectory(prefix="th06nc_friendly_") as temp_dir:
                temp_opus = Path(temp_dir) / track.name
                frames, exact_samples, packet_samples, seconds, size = convert(source, temp_opus)
                end_pos = samples48_to_pos_samples(exact_samples)
                start_pos = int(round(start_seconds * POS_RATE))
                if start_pos >= end_pos:
                    raise ToolError(
                        f"The loop start ({start_seconds:.3f}s) is after the end of this song ({seconds:.3f}s)."
                    )

                opus_backup = track.with_suffix(track.suffix + ".original.bak")
                if not opus_backup.exists():
                    shutil.copy2(track, opus_backup)
                store.backup(track.stem)

                previous_opus = track.read_bytes()
                previous_loop = store.read(track.stem)
                try:
                    shutil.copyfile(temp_opus, track)
                    store.write(track.stem, start_pos, end_pos)
                except Exception:
                    track.write_bytes(previous_opus)
                    try:
                        store.write(track.stem, previous_loop.start, previous_loop.end)
                    except Exception:
                        pass
                    raise

            self.after(0, self._replace_success, track, source, start_pos, end_pos, seconds, size, frames)
        except Exception as exc:
            self.after(0, self._replace_failed, exc)

    def _replace_success(
        self,
        track: Path,
        source: Path,
        start_pos: int,
        end_pos: int,
        seconds: float,
        size: int,
        frames: int,
    ) -> None:
        self.busy = False
        self.progress.stop()
        self.replace_button.configure(state="normal")
        self.restore_button.configure(state="normal")
        self.on_track_selected()
        start_seconds = start_pos / POS_RATE
        end_seconds = end_pos / POS_RATE
        self._set_status(
            f"✓ Done! {source.name} now replaces {track.name}. Loop: {start_seconds:.2f}s → {end_seconds:.2f}s.",
            "success",
        )
        messagebox.showinfo(
            "Music replaced successfully",
            f"{source.name} is now installed as {track.name}.\n\n"
            f"Song length: {seconds:.2f} seconds\n"
            f"Loop: {start_seconds:.2f}s → {end_seconds:.2f}s\n\n"
            "You can start the game and test it now.\n"
            "If you ever want the original back, use Restore Original.",
            parent=self,
        )

    def _replace_failed(self, exc: Exception) -> None:
        self.busy = False
        self.progress.stop()
        self.replace_button.configure(state="normal")
        self.restore_button.configure(state="normal")
        self._set_status(f"Replacement failed: {exc}", "warning")
        messagebox.showerror(
            "The music was not replaced",
            f"Nothing should have been left half-written.\n\nReason:\n{exc}",
            parent=self,
        )

    def restore_selected(self) -> None:
        if self.busy:
            return
        try:
            game = Path(self.game_root.get()).expanduser().resolve()
            track = self.selected_track()
            opus_backup = track.with_suffix(track.suffix + ".original.bak")
            if not opus_backup.is_file():
                raise ToolError("There is no original backup for this slot yet.")
            if not messagebox.askyesno(
                "Restore original music?",
                f"Restore the original {track.name} and its original loop timing?",
                parent=self,
            ):
                return

            store = PosStore(game)
            current_opus = track.read_bytes()
            current_loop = store.read(track.stem)
            try:
                shutil.copy2(opus_backup, track)
                store.restore_original(track.stem)
            except Exception:
                track.write_bytes(current_opus)
                try:
                    store.write(track.stem, current_loop.start, current_loop.end)
                except Exception:
                    pass
                raise

            self.on_track_selected()
            self._set_status(f"✓ Restored the original {track.name}.", "success")
            messagebox.showinfo("Original restored", f"{track.name} is back to its original audio and loop timing.", parent=self)
        except Exception as exc:
            self._set_status(f"Restore failed: {exc}", "warning")
            messagebox.showerror("Could not restore the track", str(exc), parent=self)

    def _set_status(self, text: str, kind: str) -> None:
        self.status_text.set(text)
        if kind == "success":
            bg, fg = SUCCESS_SOFT, SUCCESS
        elif kind == "warning":
            bg, fg = WARNING_SOFT, WARNING
        else:
            bg, fg = "#f5f1f3", MUTED
        self.status_box.configure(bg=bg)
        self.status_label.configure(bg=bg, fg=fg)



if __name__ == "__main__":
    _enable_dpi_awareness()
    FriendlyApp().mainloop()
