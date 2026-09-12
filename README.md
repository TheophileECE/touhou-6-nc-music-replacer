# Touhou 6 NC Music Replacer

A friendly Windows tool for replacing music in **Touhou Koumakyou: New Classic – the Embodiment of Scarlet Devil** without breaking the game's loop timing.

It converts common audio files to the Nintendo Opus format used by the game and updates the matching loop metadata in `th06MD.dat` automatically.

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

The first replacement of a slot creates `.original.bak` backups. **Restore Original** restores both the original Opus file and the matching loop timing for the selected soundtrack.

## Supported input

MP3, WAV, FLAC, OGG, Opus, M4A, AAC and WMA.

## Source version

Developers can clone the repository, install Python 3, and run **`Launch Touhou 6 NC Music Replacer.vbs`**. The launcher creates a local `.venv` automatically.

The repository intentionally contains **no Touhou game files, music, artwork, executables, data archives, or other extracted game assets**.

## Legal, attribution and fan-project disclaimer

This is an **unofficial, fan-made utility**. It is not affiliated with, sponsored by, approved by, or endorsed by **ZUN / Team Shanghai Alice**, **Shanghai Alice Reprise**, or **Alliance Arts**.

**Touhou Project**, **Touhou Koumakyou ~ the Embodiment of Scarlet Devil**, **Touhou Koumakyou: New Classic – the Embodiment of Scarlet Devil**, their characters, music, artwork, names, logos, and other game content remain the property of their respective rights holders.

Touhou Koumakyou: New Classic is developed by **Team Shanghai Alice / Shanghai Alice Reprise** and published by **Alliance Arts**. Alliance Arts states that the title is subject to the official **Guidelines for Touhou Project Fan Creators**: https://touhou-project.news/guidelines_en/

This project distributes only original utility code and permitted open-source dependencies. Users must provide their **own legally obtained game installation** and their own replacement audio. This tool is intended for personal modding of local files; it must not be used to redistribute original or modified game files, copyrighted music, artwork, or other assets without permission.

Third-party software bundled in the Windows executable remains under its own licenses. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Each binary release also includes a generated component report and collected third-party license files.

## License

The original source code of this utility is released under the [MIT License](LICENSE). Third-party components are **not** relicensed under MIT and remain subject to their respective licenses described in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
