from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from dialogs import RightsDialog, TutorialDialog
from ui_common import (
    ACCENT, ACCENT_HOVER, ACCENT_SOFT, BG, BORDER, CARD, DROP_BG, MUTED, TEXT,
    center_window,
)


class LayoutMixin:
    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Friendly.TCombobox",
            font=("Segoe UI", 10),
            padding=7,
            fieldbackground="white",
            background="white",
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
        )
        style.map("Friendly.TCombobox", fieldbackground=[("readonly", "white")])
        style.configure("Friendly.Horizontal.TProgressbar", troughcolor="#efe8eb", background=ACCENT, thickness=8)

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True)

        self.page_canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=self.page_canvas.yview)
        self.page_canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.page_canvas.pack(side="left", fill="both", expand=True)

        self.content = tk.Frame(self.page_canvas, bg=BG)
        self.content_window_id = self.page_canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", lambda _: self.page_canvas.configure(scrollregion=self.page_canvas.bbox("all")))
        self.page_canvas.bind("<Configure>", lambda e: self.page_canvas.itemconfigure(self.content_window_id, width=e.width))
        self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

        self.page = tk.Frame(self.content, bg=BG)
        self.page.pack(fill="both", expand=True, padx=24, pady=18)

        self.header = tk.Frame(self.page, bg=BG)
        self.header.pack(fill="x", pady=(0, 13))
        self.header.grid_columnconfigure(0, weight=1)
        self.header_text = tk.Frame(self.header, bg=BG)
        self.header_text.grid(row=0, column=0, sticky="ew")
        self.title_label = tk.Label(self.header_text, text="Touhou 6 NC Music Replacer", bg=BG, fg=TEXT, font=("Segoe UI", 21, "bold"))
        self.title_label.pack(anchor="w")
        self.subtitle_label = tk.Label(
            self.header_text,
            text="Replace a song, fix its loop automatically, and keep a safe backup of the original.",
            bg=BG,
            fg=MUTED,
            justify="left",
            wraplength=590,
            font=("Segoe UI", 9),
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        self.header_actions = tk.Frame(self.header, bg=BG)
        self.header_actions.grid(row=0, column=1, sticky="e", padx=(12, 0))
        self._button(self.header_actions, "How does this work?", lambda: TutorialDialog(self), secondary=True, compact=True).pack(side="left")
        self._button(self.header_actions, "Rights & notices", lambda: RightsDialog(self), secondary=True, compact=True).pack(side="left", padx=(7, 0))

        intro = tk.Frame(self.page, bg=ACCENT_SOFT, highlightbackground="#efcad6", highlightthickness=1)
        intro.pack(fill="x", pady=(0, 13))
        tk.Label(intro, text="No technical knowledge needed", bg=ACCENT_SOFT, fg=ACCENT, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(10, 2))
        self.intro_copy = tk.Label(
            intro,
            text="The game stores the audio and its loop instructions separately. This tool updates both together so custom songs do not jump or loop at the old track's timing.",
            bg=ACCENT_SOFT,
            fg=TEXT,
            justify="left",
            wraplength=840,
            font=("Segoe UI", 9),
        )
        self.intro_copy.pack(anchor="w", padx=16, pady=(0, 10))

        self.top_row = tk.Frame(self.page, bg=BG)
        self.top_row.pack(fill="x")
        self.top_row.grid_columnconfigure(0, weight=1, uniform="top")
        self.top_row.grid_columnconfigure(1, weight=1, uniform="top")

        self.game_card = self._card(self.top_row, "1", "Choose your game folder", "Drop the folder containing th06nc.exe here, or browse for it.")
        self.game_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.game_drop = self._drop_zone(self.game_card, "Drop Touhou 6 NC folder here", "or drop th06nc.exe")
        self.game_drop.pack(fill="x", padx=16, pady=(3, 8))
        self._register_drop(self.game_drop, self._game_dropped)
        controls = tk.Frame(self.game_card, bg=CARD)
        controls.pack(fill="x", padx=16, pady=(0, 13))
        self._button(controls, "Browse game folder", self.browse_game, compact=True).pack(side="left")
        self.game_state = tk.Label(controls, text="Not selected", bg=CARD, fg=MUTED, font=("Segoe UI", 9))
        self.game_state.pack(side="right", pady=8)

        self.track_card = self._card(self.top_row, "2", "Choose soundtrack and slot", "Choose which soundtrack version you want to modify.")
        self.track_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))

        bank_wrap = tk.Frame(self.track_card, bg=CARD)
        bank_wrap.pack(fill="x", padx=16, pady=(6, 8))
        bank_wrap.grid_columnconfigure(0, weight=1, uniform="bank")
        bank_wrap.grid_columnconfigure(1, weight=1, uniform="bank")
        self.bank_buttons["bgm"] = self._bank_button(bank_wrap, "bgm", "New Classic OST", "Remastered")
        self.bank_buttons["bgm"].grid(row=0, column=0, sticky="ew", padx=(0, 3))
        self.bank_buttons["bgm2"] = self._bank_button(bank_wrap, "bgm2", "Classic OST", "Original")
        self.bank_buttons["bgm2"].grid(row=0, column=1, sticky="ew", padx=(3, 0))
        self._refresh_bank_buttons()

        self.track_combo = ttk.Combobox(self.track_card, textvariable=self.track_choice, state="readonly", style="Friendly.TCombobox")
        self.track_combo.pack(fill="x", padx=16, pady=(0, 8))
        self.track_combo.bind("<<ComboboxSelected>>", lambda _: self.on_track_selected())
        self.track_info = tk.Label(
            self.track_card,
            text="Choose the game folder first.",
            bg=CARD,
            fg=MUTED,
            justify="left",
            wraplength=380,
            font=("Segoe UI", 9),
        )
        self.track_info.pack(anchor="w", fill="x", padx=16, pady=(0, 13))

        audio_card = self._card(self.page, "3", "Add your replacement song", "Drag in a common audio file. Nintendo Opus conversion is automatic.")
        audio_card.pack(fill="x", pady=(13, 0))
        self.audio_drop = self._drop_zone(audio_card, "Drop your song here", "MP3, WAV, FLAC, OGG, Opus, M4A, AAC or WMA")
        self.audio_drop.pack(fill="x", padx=16, pady=(3, 8))
        self._register_drop(self.audio_drop, self._audio_dropped)
        audio_controls = tk.Frame(audio_card, bg=CARD)
        audio_controls.pack(fill="x", padx=16, pady=(0, 13))
        self._button(audio_controls, "Browse for a song", self.browse_source, compact=True).pack(side="left")
        self.audio_state = tk.Label(audio_controls, text="No song selected", bg=CARD, fg=MUTED, font=("Segoe UI", 9))
        self.audio_state.pack(side="right", pady=8)

        loop_card = self._card(self.page, "4", "Choose how it loops", "The simple option is best for most custom songs.")
        loop_card.pack(fill="x", pady=(13, 0))
        choices = tk.Frame(loop_card, bg=CARD)
        choices.pack(fill="x", padx=16, pady=(4, 6))
        self._radio(choices, "whole", "Loop the whole song", "Restarts from 0:00 at the end.").pack(fill="x", pady=(0, 6))
        self._radio(choices, "custom", "Intro once, then custom loop", "Use this when an intro should play only once.").pack(fill="x")

        self.custom_loop_frame = tk.Frame(loop_card, bg=DROP_BG)
        self.custom_loop_frame.grid_columnconfigure(4, weight=1)
        tk.Label(self.custom_loop_frame, text="Loop starts at", bg=DROP_BG, fg=TEXT, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=(12, 6), pady=8)
        loop_entry = tk.Entry(self.custom_loop_frame, textvariable=self.loop_start, font=("Segoe UI", 10), width=10, relief="solid", bd=1, highlightthickness=0)
        loop_entry.grid(row=0, column=1, pady=8)
        tk.Label(self.custom_loop_frame, text="seconds", bg=DROP_BG, fg=MUTED, font=("Segoe UI", 9)).grid(row=0, column=2, padx=6)
        self._button(self.custom_loop_frame, "Use original start", self.use_original_start, secondary=True, compact=True).grid(row=0, column=5, padx=8, pady=6)
        self._update_loop_mode()
        self.loop_mode.trace_add("write", lambda *_: self._update_loop_mode())

        self.action_card = tk.Frame(self.page, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        self.action_card.pack(fill="x", pady=(13, 0))
        self.action_top = tk.Frame(self.action_card, bg=CARD)
        self.action_top.pack(fill="x", padx=16, pady=(13, 8))
        self.action_top.grid_columnconfigure(0, weight=1)
        self.action_copy = tk.Frame(self.action_top, bg=CARD)
        self.action_copy.grid(row=0, column=0, sticky="ew")
        self.action_heading = tk.Label(self.action_copy, text="Ready when you are", bg=CARD, fg=TEXT, font=("Segoe UI", 14, "bold"))
        self.action_heading.pack(anchor="w")
        self.action_subtitle = tk.Label(
            self.action_copy,
            text="Original files are backed up automatically the first time you replace a slot.",
            bg=CARD,
            fg=MUTED,
            justify="left",
            wraplength=590,
            font=("Segoe UI", 9),
        )
        self.action_subtitle.pack(anchor="w", pady=(2, 0))
        self.replace_button = self._button(self.action_top, "Replace Music", self.start_replace, big=True)
        self.replace_button.grid(row=0, column=1, sticky="e", padx=(14, 0))

        self.progress = ttk.Progressbar(self.action_card, mode="indeterminate", style="Friendly.Horizontal.TProgressbar")
        self.progress.pack(fill="x", padx=16, pady=(0, 8))

        self.status_box = tk.Frame(self.action_card, bg="#f5f1f3")
        self.status_box.pack(fill="x", padx=16, pady=(0, 13))
        self.status_label = tk.Label(
            self.status_box,
            textvariable=self.status_text,
            bg="#f5f1f3",
            fg=MUTED,
            justify="left",
            wraplength=720,
            font=("Segoe UI", 9),
        )
        self.status_label.pack(side="left", fill="x", expand=True, padx=12, pady=9)
        self.restore_button = self._button(self.status_box, "Restore Original", self.restore_selected, secondary=True, compact=True)
        self.restore_button.pack(side="right", padx=8, pady=5)

        self.after_idle(lambda: self._apply_responsive_layout(self.winfo_width()))

    def _card(self, parent: tk.Misc, number: str, title: str, subtitle: str) -> tk.Frame:
        card = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        heading = tk.Frame(card, bg=CARD)
        heading.pack(fill="x", padx=16, pady=(13, 5))
        badge = tk.Label(heading, text=number, bg=ACCENT, fg="white", font=("Segoe UI", 9, "bold"), width=3, height=1)
        badge.pack(side="left", padx=(0, 9))
        copy = tk.Frame(heading, bg=CARD)
        copy.pack(side="left", fill="x", expand=True)
        tk.Label(copy, text=title, bg=CARD, fg=TEXT, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(copy, text=subtitle, bg=CARD, fg=MUTED, font=("Segoe UI", 8), wraplength=700, justify="left").pack(anchor="w", pady=(1, 0))
        return card

    def _drop_zone(self, parent: tk.Misc, title: str, subtitle: str) -> tk.Frame:
        zone = tk.Frame(parent, bg=DROP_BG, highlightbackground="#d9cdd2", highlightthickness=2, cursor="hand2")
        icon = tk.Label(zone, text="+", bg=DROP_BG, fg=ACCENT, font=("Segoe UI", 20, "bold"))
        icon.pack(pady=(8, 0))
        title_label = tk.Label(zone, text=title, bg=DROP_BG, fg=TEXT, font=("Segoe UI", 10, "bold"))
        title_label.pack()
        subtitle_label = tk.Label(zone, text=subtitle, bg=DROP_BG, fg=MUTED, font=("Segoe UI", 8))
        subtitle_label.pack(pady=(1, 8))
        self.drop_parts[zone] = {
            "icon": icon,
            "title": title_label,
            "subtitle": subtitle_label,
            "default_title": title,
            "default_subtitle": subtitle,
        }
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
    ) -> tk.Button:
        if secondary:
            bg, fg, active = "#f1ebee", TEXT, "#e7dfe3"
        else:
            bg, fg, active = ACCENT, "white", ACCENT_HOVER
        if big:
            font, padx, pady = ("Segoe UI", 11, "bold"), 24, 10
        elif compact:
            font, padx, pady = ("Segoe UI", 8, "bold"), 11, 6
        else:
            font, padx, pady = ("Segoe UI", 9, "bold"), 15, 8
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

    def _bank_button(self, parent: tk.Misc, bank: str, title: str, path_hint: str) -> tk.Button:
        return tk.Button(
            parent,
            text=f"{title}\n{path_hint}",
            command=lambda: self.set_music_bank(bank),
            justify="center",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=8,
            pady=7,
            cursor="hand2",
        )

    def _radio(self, parent: tk.Misc, value: str, title: str, subtitle: str) -> tk.Frame:
        frame = tk.Frame(parent, bg=DROP_BG, highlightthickness=1, highlightbackground=BORDER)
        radio = tk.Radiobutton(
            frame,
            variable=self.loop_mode,
            value=value,
            bg=DROP_BG,
            activebackground=DROP_BG,
            selectcolor=DROP_BG,
            fg=ACCENT,
            font=("Segoe UI", 9, "bold"),
        )
        radio.pack(side="left", padx=(10, 6), pady=10)
        copy = tk.Frame(frame, bg=DROP_BG)
        copy.pack(side="left", fill="x", expand=True, pady=7)
        tk.Label(copy, text=title, bg=DROP_BG, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(copy, text=subtitle, bg=DROP_BG, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w", pady=(1, 0))
        return frame

    def _on_mousewheel(self, event):
        widget = self.winfo_containing(event.x_root, event.y_root)
        if widget is None or not self._is_descendant(widget, self.content):
            return None
        widget_class = widget.winfo_class()
        if widget_class in {"Listbox", "TCombobox", "Scrollbar", "TScrollbar"}:
            return None
        delta = int(-1 * (event.delta / 120)) if event.delta else 0
        if delta:
            self.page_canvas.yview_scroll(delta, "units")
            return "break"
        return None

    @staticmethod
    def _is_descendant(widget: tk.Misc, ancestor: tk.Misc) -> bool:
        current: tk.Misc | None = widget
        while current is not None:
            if current == ancestor:
                return True
            try:
                parent_name = current.winfo_parent()
                if not parent_name:
                    return False
                current = current._nametowidget(parent_name)  # type: ignore[attr-defined]
            except Exception:
                return False
        return False

    def _on_resize(self, event) -> None:
        if event.widget is self:
            self.after_idle(lambda: self._apply_responsive_layout(event.width))

    def _apply_responsive_layout(self, width: int) -> None:
        compact = width < 860
        if compact != self._compact_layout:
            self._compact_layout = compact
            self.header_actions.grid_forget()
            self.game_card.grid_forget()
            self.track_card.grid_forget()
            self.replace_button.grid_forget()
            if compact:
                self.header_actions.grid(row=1, column=0, sticky="w", pady=(9, 0))
                self.game_card.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=0, pady=(0, 7))
                self.track_card.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=0)
                self.replace_button.grid(row=1, column=0, sticky="w", pady=(9, 0))
            else:
                self.header_actions.grid(row=0, column=1, sticky="e", padx=(12, 0))
                self.game_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
                self.track_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
                self.replace_button.grid(row=0, column=1, sticky="e", padx=(14, 0))

        content_width = max(460, width - (68 if compact else 90))
        self.subtitle_label.configure(wraplength=max(360, content_width - (20 if compact else 300)))
        self.intro_copy.configure(wraplength=max(420, content_width - 30))
        self.action_subtitle.configure(wraplength=max(360, content_width - (40 if compact else 280)))
        self.status_label.configure(wraplength=max(360, content_width - 150))
        self.track_info.configure(wraplength=max(310, content_width - 40) if compact else max(300, content_width // 2 - 55))
