from __future__ import annotations

import tkinter as tk
import webbrowser
from tkinter import ttk

BG = "#f7f4f6"
CARD = "#ffffff"
TEXT = "#2b2528"
MUTED = "#6e6268"
ACCENT = "#c84367"
ACCENT_HOVER = "#ae3457"
BORDER = "#e4dce0"
RIGHTS_NOTICE_URL = "https://github.com/TheophileECE/touhou-6-nc-music-replacer/blob/main/THIRD_PARTY_NOTICES.md"
TOUHOU_GUIDELINES_URL = "https://touhou-project.news/guidelines_en/"


def center_window(window: tk.Toplevel, width: int, height: int) -> None:
    window.update_idletasks()
    x = max(0, (window.winfo_screenwidth() - width) // 2)
    y = max(0, (window.winfo_screenheight() - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


class TutorialDialog(tk.Toplevel):
    PAGES = [
        ("Welcome", "This tool replaces Touhou 6 New Classic music without leaving the old song's loop points behind. You only need your game folder and a replacement song."),
        ("1. Choose the game", "Drag the folder that contains th06nc.exe onto the first box, or click Browse. The tool checks the soundtrack files and loop metadata before it lets you continue."),
        ("2. Pick soundtrack, slot and song", "Choose New Classic OST or Classic OST, select the Touhou track you want to replace, then drag in an MP3, WAV, FLAC, OGG, Opus, M4A, AAC or WMA file."),
        ("3. Looping made simple", "For most custom music, leave 'Loop the whole song' selected. Advanced users can choose a custom loop start so an intro plays only once."),
        ("4. Safe replacement", "Click Replace Music. The first time a slot is changed, the original Opus and loop metadata are backed up as .original.bak. Restore Original puts that slot back exactly as it was."),
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
        body.pack(fill="both", expand=True, padx=20, pady=20)
        self.step = tk.Label(body, bg=CARD, fg=ACCENT, font=("Segoe UI", 9, "bold"))
        self.step.pack(anchor="w", padx=22, pady=(20, 3))
        self.heading = tk.Label(body, bg=CARD, fg=TEXT, font=("Segoe UI", 18, "bold"))
        self.heading.pack(anchor="w", padx=22)
        self.copy = tk.Label(body, bg=CARD, fg=MUTED, justify="left", wraplength=520, font=("Segoe UI", 10))
        self.copy.pack(anchor="w", fill="x", padx=22, pady=(12, 20))

        nav = tk.Frame(body, bg=CARD)
        nav.pack(fill="x", padx=22, pady=(0, 20))
        self.back_btn = tk.Button(nav, text="Back", command=self.back, font=("Segoe UI", 9, "bold"), relief="flat", padx=15, pady=7)
        self.back_btn.pack(side="left")
        self.next_btn = tk.Button(nav, text="Next", command=self.next, bg=ACCENT, activebackground=ACCENT_HOVER, fg="white", activeforeground="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=20, pady=7, cursor="hand2")
        self.next_btn.pack(side="right")
        self.show_page()
        center_window(self, 610, 330)

    def show_page(self) -> None:
        title, copy = self.PAGES[self.index]
        self.step.configure(text=f"STEP {self.index + 1} OF {len(self.PAGES)}")
        self.heading.configure(text=title)
        self.copy.configure(text=copy)
        self.back_btn.configure(state="normal" if self.index else "disabled")
        self.next_btn.configure(text="Got it" if self.index == len(self.PAGES) - 1 else "Next")

    def back(self) -> None:
        if self.index:
            self.index -= 1
            self.show_page()

    def next(self) -> None:
        if self.index == len(self.PAGES) - 1:
            self.destroy()
        else:
            self.index += 1
            self.show_page()


class RightsDialog(tk.Toplevel):
    NOTICE = """ABOUT THIS FAN-MADE TOOL

Touhou 6 NC Music Replacer is an unofficial fan-made utility. It is not affiliated with, sponsored by, approved by, or endorsed by ZUN / Team Shanghai Alice, Shanghai Alice Reprise, or Alliance Arts.

TOUHOU / NEW CLASSIC RIGHTS AND CREDITS

Touhou Project and Touhou Koumakyou ~ the Embodiment of Scarlet Devil originate from ZUN / Team Shanghai Alice. Touhou Koumakyou: New Classic – the Embodiment of Scarlet Devil is developed by Team Shanghai Alice / Shanghai Alice Reprise and published by Alliance Arts. The games, characters, music, artwork, names, logos, and other game content remain the property of their respective rights holders.

WHAT THIS TOOL DISTRIBUTES

This project does not include Touhou or New Classic game executables, music, artwork, screenshots, data archives, or extracted game assets. You must provide your own legally obtained game installation and your own replacement audio. The tool is intended for personal modification of local files, not redistribution of copyrighted game assets.

OPEN-SOURCE COMPONENTS

The Windows build also contains open-source runtime components such as Python, Tcl/Tk, tkinterdnd2 / TkDND, imageio-ffmpeg, FFmpeg and the PyInstaller bootloader. Those components remain under their respective licenses. Exact versions, FFmpeg build information, attribution, license files and source links are published with each GitHub release.

The current Windows release uses an FFmpeg build that identifies itself as GPL v3-or-later. The full third-party notice and exact build report are the authoritative references for release-specific details.

Thank you to ZUN / Team Shanghai Alice, Shanghai Alice Reprise, Alliance Arts, and the open-source projects that make this fan utility possible."""

    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.title("Rights, credits & notices")
        self.configure(bg=BG)
        self.transient(parent)
        self.grab_set()
        self.minsize(560, 420)

        card = tk.Frame(self, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(card, text="Rights, credits & notices", bg=CARD, fg=TEXT, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=20, pady=(18, 3))
        tk.Label(card, text="A concise explanation of the project's unofficial status, rights holders and bundled open-source software.", bg=CARD, fg=MUTED, justify="left", wraplength=620, font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(0, 12))

        text_wrap = tk.Frame(card, bg=CARD)
        text_wrap.pack(fill="both", expand=True, padx=20)
        notice = tk.Text(text_wrap, wrap="word", relief="flat", bd=0, bg="#fbf8f9", fg=TEXT, font=("Segoe UI", 9), padx=14, pady=12, cursor="arrow")
        notice.insert("1.0", self.NOTICE)
        notice.configure(state="disabled")
        scroll = ttk.Scrollbar(text_wrap, orient="vertical", command=notice.yview)
        notice.configure(yscrollcommand=scroll.set)
        notice.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        actions = tk.Frame(card, bg=CARD)
        actions.pack(fill="x", padx=20, pady=16)
        self._button(actions, "Touhou fan-creator guidelines", lambda: webbrowser.open(TOUHOU_GUIDELINES_URL), secondary=True).pack(side="left")
        self._button(actions, "Full third-party notices", lambda: webbrowser.open(RIGHTS_NOTICE_URL), secondary=True).pack(side="left", padx=8)
        self._button(actions, "Close", self.destroy).pack(side="right")
        center_window(self, 720, 540)

    @staticmethod
    def _button(parent: tk.Misc, text: str, command, secondary: bool = False) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg="#f1ebee" if secondary else ACCENT,
            activebackground="#e7dfe3" if secondary else ACCENT_HOVER,
            fg=TEXT if secondary else "white",
            activeforeground=TEXT if secondary else "white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=13 if secondary else 18,
            pady=7,
            cursor="hand2",
        )
