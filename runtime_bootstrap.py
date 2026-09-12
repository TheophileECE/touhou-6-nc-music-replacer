from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

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
        [str(_venv_pythonw()), str(BASE / "app.pyw")],
        cwd=str(BASE),
        creationflags=_hidden_flags(),
    )


class FirstRunSetup(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Touhou 6 NC Music Replacer")
        self.configure(bg="#f7f4f6")
        self.resizable(False, False)
        self.geometry("500x245")
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 245) // 2
        self.geometry(f"500x245+{max(0, x)}+{max(0, y)}")

        card = tk.Frame(self, bg="white", highlightbackground="#e4dce0", highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(card, text="First-time setup", bg="white", fg="#2b2528", font=("Segoe UI", 17, "bold")).pack(anchor="w", padx=22, pady=(22, 5))
        tk.Label(
            card,
            text="Preparing drag-and-drop and the audio converter. Everything stays inside this tool's folder.",
            bg="white",
            fg="#6e6268",
            justify="left",
            wraplength=410,
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=22)
        self.status = tk.StringVar(value="Preparing the app…")
        tk.Label(card, textvariable=self.status, bg="white", fg="#c84367", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=22, pady=(16, 6))
        self.progress = ttk.Progressbar(card, mode="indeterminate")
        self.progress.pack(fill="x", padx=22, pady=(0, 22))
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


def ensure_runtime() -> None:
    if getattr(sys, "frozen", False) or _running_in_private_env():
        return
    if READY.is_file() and _venv_python().is_file():
        _launch_private_app()
        raise SystemExit
    FirstRunSetup().mainloop()
    raise SystemExit
