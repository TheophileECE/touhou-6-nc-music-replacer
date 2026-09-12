# Third-Party Notices and Legal Disclaimer

Last reviewed: 2026-09-12

This file records attribution and licensing information for software and intellectual property referenced by or bundled with **Touhou 6 NC Music Replacer**. It is provided for transparency and compliance and is not legal advice.

## Touhou Project / New Classic attribution

Touhou 6 NC Music Replacer is an **unofficial fan-made utility**. It is not affiliated with, sponsored by, approved by, or endorsed by **ZUN / Team Shanghai Alice**, **Shanghai Alice Reprise**, or **Alliance Arts**.

**Touhou Project**, **Touhou Koumakyou ~ the Embodiment of Scarlet Devil**, **Touhou Koumakyou: New Classic – the Embodiment of Scarlet Devil**, and their characters, music, artwork, names, logos, and other game content remain the property of their respective rights holders.

Touhou Koumakyou: New Classic – the Embodiment of Scarlet Devil is developed by **Team Shanghai Alice / Shanghai Alice Reprise** and published by **Alliance Arts**.

Alliance Arts states that this title is subject to the official **Guidelines for Touhou Project Fan Creators**:

https://touhou-project.news/guidelines_en/

This repository and its releases intentionally do **not** distribute original Touhou or New Classic game files, music, artwork, screenshots, executables, data archives, or other extracted game assets. Users must provide their own legally obtained game installation and their own replacement audio. The utility is intended for personal modification of local files and must not be used as a means to redistribute original or modified copyrighted game assets without permission.

## Project source license

The original source code written specifically for Touhou 6 NC Music Replacer is licensed under the repository's [MIT License](LICENSE).

That MIT license applies only to the project's own original code. Third-party components listed below remain under their own licenses and are not relicensed under the project's MIT license.

## Third-party software in the Windows executable

The standalone Windows build is produced with PyInstaller and may bundle the following components directly or as supporting runtime files:

| Component | Purpose | License / terms | Upstream |
| --- | --- | --- | --- |
| Python 3.12 runtime | Runs the application | Python Software Foundation License Version 2 and incorporated-software notices | https://www.python.org/ |
| Tcl/Tk | Tkinter graphical interface | Tcl/Tk BSD-style license | https://www.tcl-lang.org/software/tcltk/license.html |
| tkinterdnd2 | Drag-and-drop Python wrapper | MIT License, copyright © 2020 Philippe Gagné | https://github.com/Eliav2/tkinterdnd2 |
| TkDND | Native Tk drag-and-drop extension bundled by tkinterdnd2 | Permissive Tk/Tcl-style license; copyright notices retained by upstream | https://github.com/petasis/tkdnd |
| imageio-ffmpeg | Locates and invokes the bundled FFmpeg executable | BSD 2-Clause License, copyright © 2019-2025 imageio | https://github.com/imageio/imageio-ffmpeg |
| FFmpeg | Audio decoding and Opus encoding | FFmpeg is LGPL 2.1-or-later by default; builds using optional GPL components are GPL 2-or-later. The exact license/build configuration of the distributed binary is recorded for every release. | https://ffmpeg.org/ |
| PyInstaller bootloader | Packages the Python program into the standalone executable | GPL 2-or-later with the PyInstaller Bootloader Exception | https://pyinstaller.org/ |

### Exact release contents

Every Windows release publishes two additional compliance artifacts next to the executable:

- **`BUNDLED_COMPONENTS.txt`** — records the exact Python/package versions, the bundled FFmpeg binary SHA-256, and the output of `ffmpeg -version` and `ffmpeg -L` from the build environment.
- **`THIRD_PARTY_LICENSES.zip`** — collects license/copyright files supplied by Python and the installed third-party packages, plus the FFmpeg runtime license output and this notice.

These generated files are the best reference for the exact third-party versions and license material contained in a particular release.

## FFmpeg-specific notice

The Windows executable uses the FFmpeg binary distributed by the platform-specific `imageio-ffmpeg` wheel. `imageio-ffmpeg` documents that its platform wheels include an FFmpeg executable. Touhou 6 NC Music Replacer does not modify FFmpeg.

FFmpeg's effective license depends on how that particular binary was configured. The release build therefore records the binary's own `-version` and `-L` output rather than assuming a license variant.

FFmpeg project licensing information:

https://ffmpeg.org/legal.html

FFmpeg source code:

https://ffmpeg.org/download.html

The upstream repository used by imageio-ffmpeg for its packaged FFmpeg binaries is:

https://github.com/imageio/imageio-binaries/tree/master/ffmpeg

## PyInstaller notice

PyInstaller itself is GPL 2-or-later. Its published **Bootloader Exception** grants permission to embed and distribute the compiled bootloader in combination with other programs without imposing the GPL on the combined application solely because the bootloader is used.

Upstream licensing terms:

https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt

## No endorsement

References to third-party projects, companies, products, trademarks, or copyright holders are solely for identification, interoperability, attribution, and license compliance. No endorsement, sponsorship, partnership, or official status is claimed or implied.
