from __future__ import annotations

import math
import shutil
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from tkinterdnd2 import DND_FILES
from core import POS_RATE, TRACK_TITLES, PosStore, ToolError, convert, parse_track_number, samples48_to_pos_samples
from ui_common import (
    ACCENT, ACCENT_HOVER, AUDIO_TYPES, BORDER, DROP_BG, ERROR, MUTED, SUCCESS,
    SUCCESS_SOFT, TEXT, WARNING, WARNING_SOFT,
)


class ActionsMixin:
    @staticmethod
    def _bank_label(bank: str) -> str:
        return "Classic OST" if bank == "bgm2" else "New Classic OST"

    def _refresh_bank_buttons(self) -> None:
        active = self.music_bank.get()
        for bank, button in self.bank_buttons.items():
            selected = bank == active
            button.configure(
                bg=ACCENT if selected else "#f1ebee",
                activebackground=ACCENT_HOVER if selected else "#e7dfe3",
                fg="white" if selected else TEXT,
                activeforeground="white" if selected else TEXT,
            )

    def set_music_bank(self, bank: str) -> None:
        if self.busy or bank not in {"bgm", "bgm2"} or self.music_bank.get() == bank:
            return
        self.music_bank.set(bank)
        self._refresh_bank_buttons()
        if self.game_root.get().strip():
            self.scan_game(show_error=False)
        else:
            self.track_paths.clear()
            self.track_combo["values"] = []
            self.track_choice.set("")
            self.current_loop = None
            self.track_info.configure(text=f"{self._bank_label(bank)} selected. Choose the game folder first.", fg=MUTED)

    def _register_drop(self, widget: tk.Frame, handler) -> None:
        targets = (widget, *widget.winfo_children())
        for target in targets:
            try:
                target.drop_target_register(DND_FILES)  # type: ignore[attr-defined]
                target.dnd_bind("<<DropEnter>>", lambda event, zone=widget: self._drop_enter(event, zone))  # type: ignore[attr-defined]
                target.dnd_bind("<<DropLeave>>", lambda event, zone=widget: self._drop_leave(event, zone))  # type: ignore[attr-defined]
                target.dnd_bind("<<Drop>>", lambda event, zone=widget, callback=handler: self._drop_dispatch(event, zone, callback))  # type: ignore[attr-defined]
            except Exception:
                pass

    def _drop_enter(self, event, zone: tk.Frame):
        self._set_drop_visual(zone, "active", "Drop it here", "Release to select this item")
        return getattr(event, "action", None)

    def _drop_leave(self, event, zone: tk.Frame):
        self._restore_drop_visual(zone)
        return getattr(event, "action", None)

    def _drop_dispatch(self, event, zone: tk.Frame, handler):
        result = handler(event)
        self._restore_drop_visual(zone)
        return result

    def _set_drop_visual(self, zone: tk.Frame, state: str, title: str | None = None, subtitle: str | None = None) -> None:
        parts = self.drop_parts.get(zone)
        if not parts:
            return
        if state == "active":
            bg, border, icon_text, icon_fg = "#fff3f7", ACCENT, "↓", ACCENT
        elif state == "success":
            bg, border, icon_text, icon_fg = SUCCESS_SOFT, "#8fc2aa", "✓", SUCCESS
        elif state == "warning":
            bg, border, icon_text, icon_fg = WARNING_SOFT, "#d9b26f", "!", WARNING
        else:
            bg, border, icon_text, icon_fg = DROP_BG, "#d9cdd2", "+", ACCENT
        zone.configure(bg=bg, highlightbackground=border)
        icon = parts["icon"]
        title_label = parts["title"]
        subtitle_label = parts["subtitle"]
        assert isinstance(icon, tk.Label) and isinstance(title_label, tk.Label) and isinstance(subtitle_label, tk.Label)
        icon.configure(text=icon_text, bg=bg, fg=icon_fg)
        title_label.configure(text=title or str(parts["default_title"]), bg=bg, fg=SUCCESS if state == "success" else TEXT)
        subtitle_label.configure(text=subtitle or str(parts["default_subtitle"]), bg=bg, fg=MUTED)

    def _restore_drop_visual(self, zone: tk.Frame) -> None:
        if zone is self.game_drop and self.game_root.get().strip() and self.track_paths:
            path = Path(self.game_root.get())
            self._set_drop_visual(zone, "success", "Game ready", path.name or str(path))
        elif zone is self.audio_drop and self.source_file.get().strip():
            path = Path(self.source_file.get())
            self._set_drop_visual(zone, "success", "Song ready", path.name)
        else:
            self._set_drop_visual(zone, "default")

    def _flash_drop_warning(self, zone: tk.Frame, title: str, subtitle: str) -> None:
        self._set_drop_visual(zone, "warning", title, subtitle)
        self.after(1600, lambda: self._restore_drop_visual(zone))

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
            self._flash_drop_warning(self.game_drop, "Not a game folder", "Drop the folder containing th06nc.exe")
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
            self._flash_drop_warning(self.audio_drop, "Unsupported file", "Try MP3, WAV, FLAC, OGG, Opus, M4A, AAC or WMA")
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
        path = path.resolve()
        self.source_file.set(str(path))
        self.audio_state.configure(text=f"✓ {path.name}", fg=SUCCESS)
        self._set_drop_visual(self.audio_drop, "success", "Song ready", path.name)
        self._set_status(f"Song selected: {path.name}. Choose a track slot, then replace it when ready.", "success")

    def scan_game(self, *, show_error: bool = True) -> None:
        bank = self.music_bank.get()
        try:
            game = Path(self.game_root.get()).expanduser().resolve()
            if not (game / "th06nc.exe").is_file():
                raise ToolError("This folder does not contain th06nc.exe.")
            bgm = game / "data" / bank
            if not bgm.is_dir():
                raise ToolError(f"The game folder is missing data/{bank}.")
            tracks = sorted(bgm.glob("th06_*.opus"))
            if not tracks:
                raise ToolError(f"No Touhou BGM files were found in data/{bank}.")
            PosStore(game, bank)
            self.track_paths.clear()
            labels = []
            for path in tracks:
                number = parse_track_number(path.stem)
                title = TRACK_TITLES.get(number or -1, "")
                label = f"{path.stem}  —  {title}" if title else path.stem
                labels.append(label)
                self.track_paths[label] = path
            self.track_combo["values"] = labels
            self.track_choice.set(labels[0])
            self.game_state.configure(text=f"✓ {self._bank_label(bank)} · {len(tracks)} tracks", fg=SUCCESS)
            self._set_drop_visual(self.game_drop, "success", "Game ready", game.name or str(game))
            self.on_track_selected()
            self._set_status(f"{self._bank_label(bank)} selected. Choose the music slot you want to replace.", "success")
        except Exception as exc:
            self.track_paths.clear()
            self.track_combo["values"] = []
            self.track_choice.set("")
            self.current_loop = None
            self.game_state.configure(text=f"{self._bank_label(bank)} unavailable", fg=ERROR)
            self.track_info.configure(text=f"Could not load {self._bank_label(bank)}: {exc}", fg=MUTED)
            self._flash_drop_warning(self.game_drop, "Could not use this folder", str(exc))
            self._set_status(str(exc), "warning")
            if show_error:
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
            bank = self.music_bank.get()
            info = PosStore(game, bank).read(track.stem)
            self.current_loop = info
            self.track_info.configure(
                text=f"{self._bank_label(bank)} loop: {info.start_seconds:.2f}s → {info.end_seconds:.2f}s\n"
                "Replacement timing is updated automatically.",
                fg=MUTED,
            )
        except Exception as exc:
            self.current_loop = None
            self.track_info.configure(text=f"Loop information could not be read: {exc}", fg=ERROR)

    def _update_loop_mode(self) -> None:
        if self.loop_mode.get() == "custom":
            self.custom_loop_frame.pack(fill="x", padx=16, pady=(2, 13))
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
            bank = self.music_bank.get()
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
            f"Replace {self._bank_label(bank)} / {track.name} with:\n\n{source.name}\n\n"
            f"Loop from: {loop_copy}\n\n"
            "The original track and loop metadata will be backed up automatically.",
            parent=self,
        ):
            return

        self.busy = True
        self.replace_button.configure(state="disabled", text="Converting…")
        self.restore_button.configure(state="disabled")
        for button in self.bank_buttons.values():
            button.configure(state="disabled")
        self.action_heading.configure(text="Working on your replacement…", fg=ACCENT)
        self.action_card.configure(highlightbackground="#efcad6")
        self.progress.start(12)
        self._set_status("Converting your song to the format used by Touhou 6 NC…", "neutral")
        threading.Thread(target=self._replace_worker, args=(game, bank, track, source, loop_start), daemon=True).start()

    def _replace_worker(self, game: Path, bank: str, track: Path, source: Path, start_seconds: float) -> None:
        try:
            store = PosStore(game, bank)
            with tempfile.TemporaryDirectory(prefix="th06nc_friendly_") as temp_dir:
                temp_opus = Path(temp_dir) / track.name
                frames, exact_samples, _packet_samples, seconds, size = convert(source, temp_opus)
                end_pos = samples48_to_pos_samples(exact_samples)
                start_pos = int(round(start_seconds * POS_RATE))
                if start_pos >= end_pos:
                    raise ToolError(f"The loop start ({start_seconds:.3f}s) is after the end of this song ({seconds:.3f}s).")

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

            self.after(0, self._replace_success, bank, track, source, start_pos, end_pos, seconds, size, frames)
        except Exception as exc:
            self.after(0, self._replace_failed, exc)

    def _replace_success(
        self,
        bank: str,
        track: Path,
        source: Path,
        start_pos: int,
        end_pos: int,
        seconds: float,
        size: int,
        frames: int,
    ) -> None:
        del size, frames
        self.busy = False
        self.progress.stop()
        self.replace_button.configure(state="normal", text="Done ✓", bg=SUCCESS, activebackground="#27684d")
        self.restore_button.configure(state="normal")
        for button in self.bank_buttons.values():
            button.configure(state="normal")
        self.action_heading.configure(text="Music replaced successfully", fg=SUCCESS)
        self.action_card.configure(highlightbackground="#8fc2aa")
        self.on_track_selected()
        start_seconds = start_pos / POS_RATE
        end_seconds = end_pos / POS_RATE
        self._set_status(
            f"✓ {source.name} now replaces {self._bank_label(bank)} / {track.name}. Loop: {start_seconds:.2f}s → {end_seconds:.2f}s. You can launch the game and test it.",
            "success",
        )
        self.after(3000, self._reset_action_feedback)
        messagebox.showinfo(
            "Music replaced successfully",
            f"{source.name} is now installed as {self._bank_label(bank)} / {track.name}.\n\n"
            f"Song length: {seconds:.2f} seconds\n"
            f"Loop: {start_seconds:.2f}s → {end_seconds:.2f}s\n\n"
            "You can start the game and test it now.\n"
            "If you ever want the original back, use Restore Original.",
            parent=self,
        )

    def _replace_failed(self, exc: Exception) -> None:
        self.busy = False
        self.progress.stop()
        self.replace_button.configure(state="normal", text="Replace Music", bg=ACCENT, activebackground=ACCENT_HOVER)
        self.restore_button.configure(state="normal")
        for button in self.bank_buttons.values():
            button.configure(state="normal")
        self.action_heading.configure(text="Replacement could not finish", fg=WARNING)
        self.action_card.configure(highlightbackground="#d9b26f")
        self._set_status(f"Replacement failed: {exc}", "warning")
        self.after(3000, self._reset_action_feedback)
        messagebox.showerror(
            "The music was not replaced",
            f"Nothing should have been left half-written.\n\nReason:\n{exc}",
            parent=self,
        )

    def _reset_action_feedback(self) -> None:
        if self.busy:
            return
        self.action_heading.configure(text="Ready when you are", fg=TEXT)
        self.action_card.configure(highlightbackground=BORDER)
        self.replace_button.configure(text="Replace Music", bg=ACCENT, activebackground=ACCENT_HOVER)

    def restore_selected(self) -> None:
        if self.busy:
            return
        try:
            game = Path(self.game_root.get()).expanduser().resolve()
            bank = self.music_bank.get()
            track = self.selected_track()
            opus_backup = track.with_suffix(track.suffix + ".original.bak")
            if not opus_backup.is_file():
                raise ToolError("There is no original backup for this slot yet.")
            if not messagebox.askyesno(
                "Restore original music?",
                f"Restore the original {self._bank_label(bank)} / {track.name} and its original loop timing?",
                parent=self,
            ):
                return

            store = PosStore(game, bank)
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
            self.action_heading.configure(text="Original track restored", fg=SUCCESS)
            self.action_card.configure(highlightbackground="#8fc2aa")
            self._set_status(f"✓ Restored the original {self._bank_label(bank)} / {track.name}.", "success")
            self.after(3000, self._reset_action_feedback)
            messagebox.showinfo(
                "Original restored",
                f"{self._bank_label(bank)} / {track.name} is back to its original audio and loop timing.",
                parent=self,
            )
        except Exception as exc:
            self._set_status(f"Restore failed: {exc}", "warning")
            messagebox.showerror("Could not restore the track", str(exc), parent=self)

    def _set_status(self, text: str, kind: str) -> None:
        self.status_text.set(text)
        self.status_kind = kind
        if kind == "success":
            bg, fg = SUCCESS_SOFT, SUCCESS
        elif kind == "warning":
            bg, fg = WARNING_SOFT, WARNING
        else:
            bg, fg = "#f5f1f3", MUTED
        self.status_box.configure(bg=bg)
        self.status_label.configure(bg=bg, fg=fg)
