# Touhou 6 NC Music Replacer

A friendly Windows tool for replacing music in **Touhou 6 New Classic** without breaking the game's loop timing.

It converts common audio files to the Nintendo Opus format used by the game and updates the matching loop metadata in `th06MD.dat` automatically.

> **v1.1 development branch:** adds separate **New Classic OST / Classic OST** selection. Internally, the matching loop metadata is adjusted automatically for whichever soundtrack is selected.

## Download

For normal use, download **`Touhou 6 NC Music Replacer.exe`** from the [latest release](https://github.com/TheophileECE/touhou-6-nc-music-replacer/releases/latest).

No Python installation is required for the release build.

## Use

1. Run **`Touhou 6 NC Music Replacer.exe`**.
2. Choose or drag in the folder containing `th06nc.exe`.
3. Choose **New Classic OST** or **Classic OST**, then pick the music slot to replace.
4. Drag in your replacement song.
5. Leave **Loop the whole song** selected unless you want a non-repeating intro.
6. Click **Replace Music**.

The first replacement of a slot creates `.original.bak` backups. **Restore Original** restores both the original Opus file and the matching loop timing for the selected music bank.

## Supported input

MP3, WAV, FLAC, OGG, Opus, M4A, AAC and WMA.

## Source version

Developers can clone the repository, install Python 3, and run **`Launch Touhou 6 NC Music Replacer.vbs`**. The launcher creates a local `.venv` automatically.

The repository intentionally contains **no Touhou game files, music, executables, or archives**.

## Disclaimer

This tool was built specifically around the file layout and loop metadata used by Touhou 6 New Classic. Back up your game installation before modding it.

Touhou Project is created by Team Shanghai Alice. This is an unofficial fan-made utility and is not affiliated with or endorsed by Team Shanghai Alice or the Touhou 6 New Classic developers.

## License

MIT
