# Touhou 6 NC Music Replacer

A small Windows tool for replacing music in **Touhou 6 New Classic** without breaking the game's loop timing.

The app converts common audio files to the Nintendo Opus format used by the game and updates the matching loop metadata in `th06MD.dat` automatically.

## Use

1. Download or clone this repository.
2. Install **Python 3** from [python.org](https://www.python.org/) and enable **Add Python to PATH** during installation.
3. Double-click **`Launch Touhou 6 NC Music Replacer.vbs`**.
4. Choose or drag in your game folder, select a music slot, then drag in your replacement song.
5. Leave **Loop the whole song** selected unless you specifically want a non-looping intro.
6. Click **Replace Music**.

The first launch creates a private `.venv` next to the tool and installs the two runtime dependencies. No terminal window is shown.

## Safety

The first time a track is replaced, the app keeps original backups using the `.original.bak` suffix. **Restore Original** restores both the original Opus file and its loop metadata.

The repository intentionally contains **no Touhou game files, music, executables, or archives**.

## Supported input

MP3, WAV, FLAC, OGG, Opus, M4A, AAC and WMA.

## Notes

This tool was built specifically around the file layout and loop metadata used by Touhou 6 New Classic. Back up your game installation before modding it.

Touhou Project is created by Team Shanghai Alice. This is an unofficial fan-made utility and is not affiliated with or endorsed by Team Shanghai Alice or the Touhou 6 New Classic developers.

## License

MIT
