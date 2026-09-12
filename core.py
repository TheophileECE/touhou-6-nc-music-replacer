from __future__ import annotations

import os
import shutil
import struct
import subprocess
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path

POS_RATE = 44_100
SAMPLE_RATE = 48_000
PRE_SKIP = 120
CHANNELS = 2
PACKET_BYTES = 480
FRAME_BLOCK_BYTES = PACKET_BYTES + 8
BASIC_INFO_ID = 0x80000001
DATA_INFO_ID = 0x80000004

TRACK_TITLES = {
    1: "A Dream More Scarlet than Red",
    2: "A Soul as Red as a Ground Cherry",
    3: "Apparitions Stalk the Night",
    4: "Lunate Elf",
    5: "Tomboyish Girl in Love",
    6: "Shanghai Scarlet Teahouse ~ Chinese Tea",
    7: "Shanghai Alice of Meiji 17",
    8: "Voile, the Magic Library",
    9: "Locked Girl ~ The Girl's Secret Room",
    10: "The Maid and the Pocket Watch of Blood",
    11: "Lunar Clock ~ Luna Dial",
    12: "The Young Descendant of Tepes",
    13: "Septette for a Dead Princess",
    14: "The Centennial Festival for Magical Girls",
    15: "U.N. Owen Was Her?",
    16: "An Eternity More Transient than Scarlet",
    17: "Scarlet Tower ~ Eastern Dream...",
}

MASK64 = (1 << 64) - 1
GOLDEN64 = 0x9E3779B97F4A7C15
MIX1 = 0xBF58476D1CE4E5B9
MIX2 = 0x94D049BB133111EB


class ToolError(RuntimeError):
    pass


@dataclass(frozen=True)
class _Entry:
    flags: int
    key: int
    unpacked_size: int
    stored_size: int
    file_offset: int
    name: str

    @property
    def compressed(self) -> bool:
        return bool(self.flags & 1)


def _mix64(value: int) -> int:
    value &= MASK64
    value ^= value >> 30
    value = (value * MIX1) & MASK64
    value ^= value >> 27
    value = (value * MIX2) & MASK64
    value ^= value >> 31
    return value & MASK64


def _crypt(data: bytes, seed: int) -> bytes:
    state = (seed * 0x9E3779B1 + 1) & MASK64
    state ^= (seed << 32) & MASK64
    state = (state + GOLDEN64) & MASK64
    key = struct.pack("<QQ", _mix64(state), _mix64((state + GOLDEN64) & MASK64))
    return bytes(value ^ key[index & 15] for index, value in enumerate(data))


def _archive_seed(path: Path, seed_name: str | None = None) -> int:
    name = seed_name or path.name
    stem = name.rsplit(".", 1)[0].encode("utf-8")
    return zlib.crc32(stem) & 0xFFFFFFFF


class _PkglArchive:
    def __init__(self, path: Path, *, seed_name: str | None = None):
        self.path = Path(path)
        self.seed_name = seed_name
        self.entries = self._read_entries()
        self.by_name = {entry.name.replace("\\", "/").lower(): entry for entry in self.entries}

    def _read_entries(self) -> list[_Entry]:
        with self.path.open("rb") as handle:
            header = handle.read(8)
            if len(header) != 8 or header[:4] != b"PKGL":
                raise ToolError(f"Not a PKGL archive: {self.path}")
            meta_size = struct.unpack_from("<I", header, 4)[0]
            encrypted = handle.read(meta_size)
            if len(encrypted) != meta_size:
                raise ToolError("Truncated PKGL metadata.")

        metadata = _crypt(encrypted, _archive_seed(self.path, self.seed_name))
        entries: list[_Entry] = []
        offset = 0
        while offset < len(metadata):
            if offset + 32 > len(metadata):
                raise ToolError(f"Truncated PKGL record at metadata offset 0x{offset:X}.")
            flags = struct.unpack_from("<H", metadata, offset)[0]
            key = struct.unpack_from("<I", metadata, offset + 2)[0]
            unpacked_size, stored_size, file_offset = struct.unpack_from("<QQQ", metadata, offset + 6)
            name_len = struct.unpack_from("<H", metadata, offset + 30)[0]
            end = offset + 32 + name_len
            if name_len >= 0x100 or end > len(metadata):
                raise ToolError(f"Invalid PKGL filename length at metadata offset 0x{offset:X}.")
            name = metadata[offset + 32:end].decode("utf-8", errors="strict")
            entries.append(_Entry(flags, key, unpacked_size, stored_size, file_offset, name))
            offset = end
        return entries

    def find(self, name: str) -> _Entry | None:
        normalized = name.replace("\\", "/").lower()
        exact = self.by_name.get(normalized)
        if exact:
            return exact
        basename = normalized.rsplit("/", 1)[-1]
        matches = [entry for key, entry in self.by_name.items() if key.rsplit("/", 1)[-1] == basename]
        return matches[0] if len(matches) == 1 else None

    def read_uncompressed(self, entry: _Entry) -> bytes:
        if entry.compressed:
            raise ToolError(f"{entry.name} is compressed; refusing an unsafe rewrite.")
        with self.path.open("rb") as handle:
            handle.seek(entry.file_offset)
            encrypted = handle.read(entry.stored_size)
        if len(encrypted) != entry.stored_size:
            raise ToolError(f"Truncated archive data for {entry.name}.")
        return _crypt(encrypted, entry.key)

    def write_uncompressed_same_size(self, entry: _Entry, plaintext: bytes) -> None:
        if entry.compressed:
            raise ToolError(f"{entry.name} is compressed; refusing an unsafe rewrite.")
        if len(plaintext) != entry.stored_size or len(plaintext) != entry.unpacked_size:
            raise ToolError(f"In-place replacement for {entry.name} must remain exactly {entry.stored_size} bytes.")
        encrypted = _crypt(plaintext, entry.key)
        with self.path.open("r+b") as handle:
            handle.seek(entry.file_offset)
            old = handle.read(entry.stored_size)
            try:
                handle.seek(entry.file_offset)
                handle.write(encrypted)
                handle.flush()
                os.fsync(handle.fileno())
            except Exception:
                handle.seek(entry.file_offset)
                handle.write(old)
                handle.flush()
                raise


@dataclass
class LoopInfo:
    start: int
    end: int
    location: str

    @property
    def start_seconds(self) -> float:
        return self.start / POS_RATE

    @property
    def end_seconds(self) -> float:
        return self.end / POS_RATE


class PosStore:
    def __init__(self, game_root: Path):
        self.game_root = game_root
        self.bgm_dir = game_root / "data" / "bgm"
        self.md_path = game_root / "data" / "th06MD.dat"
        self.archive = _PkglArchive(self.md_path) if self.md_path.is_file() else None

    def _loose_path(self, track_stem: str) -> Path:
        return self.bgm_dir / f"{track_stem}.pos"

    def read(self, track_stem: str) -> LoopInfo:
        loose = self._loose_path(track_stem)
        if loose.is_file():
            blob = loose.read_bytes()
            if len(blob) < 8:
                raise ToolError(f"{loose.name} is shorter than 8 bytes.")
            start, end = struct.unpack_from("<II", blob, 0)
            return LoopInfo(start, end, f"loose file: {loose}")
        if not self.archive:
            raise ToolError("Could not find data/th06MD.dat or a loose .pos file.")
        entry = self.archive.find(f"{track_stem}.pos")
        if entry is None:
            raise ToolError(f"Could not find {track_stem}.pos inside th06MD.dat.")
        blob = self.archive.read_uncompressed(entry)
        if len(blob) != 8:
            raise ToolError(f"{entry.name} is {len(blob)} bytes; expected the TH06 8-byte POS format.")
        start, end = struct.unpack("<II", blob)
        return LoopInfo(start, end, f"archive entry: {entry.name}")

    def backup(self, track_stem: str) -> list[Path]:
        backups: list[Path] = []
        loose = self._loose_path(track_stem)
        if loose.is_file():
            destination = loose.with_suffix(loose.suffix + ".original.bak")
            if not destination.exists():
                shutil.copy2(loose, destination)
            backups.append(destination)
        elif self.md_path.is_file():
            destination = self.md_path.with_suffix(self.md_path.suffix + ".original.bak")
            if not destination.exists():
                shutil.copy2(self.md_path, destination)
            backups.append(destination)
        return backups

    def write(self, track_stem: str, start: int, end: int) -> None:
        if not (0 <= start < end <= 0xFFFFFFFF):
            raise ToolError(f"Invalid loop range: {start} .. {end}")
        payload = struct.pack("<II", start, end)
        loose = self._loose_path(track_stem)
        if loose.is_file():
            old = loose.read_bytes()
            try:
                loose.write_bytes(payload if len(old) == 8 else payload + old[8:])
            except Exception:
                loose.write_bytes(old)
                raise
            return
        if not self.archive:
            raise ToolError("No writable .pos location found.")
        entry = self.archive.find(f"{track_stem}.pos")
        if entry is None:
            raise ToolError(f"Could not find {track_stem}.pos inside th06MD.dat.")
        self.archive.write_uncompressed_same_size(entry, payload)

    def restore_original(self, track_stem: str) -> None:
        loose = self._loose_path(track_stem)
        loose_backup = loose.with_suffix(loose.suffix + ".original.bak")
        if loose.is_file() and loose_backup.is_file():
            shutil.copy2(loose_backup, loose)
            return
        archive_backup = self.md_path.with_suffix(self.md_path.suffix + ".original.bak")
        if not self.archive or not archive_backup.is_file():
            raise ToolError(f"No original loop-metadata backup exists for {track_stem}.")
        original = _PkglArchive(archive_backup, seed_name=self.md_path.name)
        original_entry = original.find(f"{track_stem}.pos")
        current_entry = self.archive.find(f"{track_stem}.pos")
        if original_entry is None or current_entry is None:
            raise ToolError(f"Could not restore {track_stem}.pos from the archive backup.")
        payload = original.read_uncompressed(original_entry)
        if len(payload) != 8:
            raise ToolError(f"Backup {original_entry.name} is not an 8-byte TH06 POS entry.")
        self.archive.write_uncompressed_same_size(current_entry, payload)


def samples48_to_pos_samples(samples_48k: int) -> int:
    return (samples_48k * 441) // 480


def parse_track_number(stem: str) -> int | None:
    try:
        return int(stem.rsplit("_", 1)[1])
    except Exception:
        return None


def _ffmpeg_executable() -> str:
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    try:
        import imageio_ffmpeg  # type: ignore
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise ToolError("FFmpeg is unavailable. Relaunch the app so its local runtime can be repaired.") from exc


def _extract_ogg_packets_and_granule(path: Path) -> tuple[list[bytes], int]:
    blob = path.read_bytes()
    offset = 0
    partial = bytearray()
    packets: list[bytes] = []
    final_granule: int | None = None
    while offset < len(blob):
        if offset + 27 > len(blob) or blob[offset:offset + 4] != b"OggS":
            raise ToolError(f"Invalid Ogg page at byte 0x{offset:X}.")
        if blob[offset + 4] != 0:
            raise ToolError(f"Unsupported Ogg version {blob[offset + 4]}.")
        granule = struct.unpack_from("<Q", blob, offset + 6)[0]
        if granule != 0xFFFFFFFFFFFFFFFF:
            final_granule = granule
        segment_count = blob[offset + 26]
        table_start = offset + 27
        table_end = table_start + segment_count
        if table_end > len(blob):
            raise ToolError("Truncated Ogg segment table.")
        body_pos = table_end
        for segment_size in blob[table_start:table_end]:
            body_end = body_pos + segment_size
            if body_end > len(blob):
                raise ToolError("Truncated Ogg page body.")
            partial.extend(blob[body_pos:body_end])
            body_pos = body_end
            if segment_size < 255:
                packets.append(bytes(partial))
                partial.clear()
        offset = body_pos
    if partial:
        raise ToolError("Truncated final Ogg packet.")
    if final_granule is None:
        raise ToolError("Ogg stream contains no valid final granule position.")
    return packets, final_granule


def _encode_to_ogg(source: Path, output: Path) -> None:
    command = [
        _ffmpeg_executable(), "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source), "-map_metadata", "-1", "-vn",
        "-ac", str(CHANNELS), "-ar", str(SAMPLE_RATE),
        "-c:a", "libopus", "-application", "lowdelay",
        "-frame_duration", "20", "-b:a", "192k", "-vbr", "off",
        "-compression_level", "10", str(output),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise ToolError(f"Unable to start FFmpeg: {exc}") from exc
    if result.returncode:
        details = result.stderr.strip() or f"exit code {result.returncode}"
        raise ToolError(f"FFmpeg could not encode this track:\n{details}")


def _build_nintendo_opus(source_ogg: Path, output: Path) -> tuple[int, int, int, float, int]:
    packets, final_granule = _extract_ogg_packets_and_granule(source_ogg)
    if len(packets) < 3:
        raise ToolError("The encoded Ogg stream contains no audio packets.")
    opus_head = packets[0]
    if not opus_head.startswith(b"OpusHead") or len(opus_head) < 19:
        raise ToolError("Missing OpusHead packet.")
    if not packets[1].startswith(b"OpusTags"):
        raise ToolError("Missing OpusTags packet.")
    channels = opus_head[9]
    pre_skip = struct.unpack_from("<H", opus_head, 10)[0]
    sample_rate = struct.unpack_from("<I", opus_head, 12)[0]
    mapping_family = opus_head[18]
    if channels != CHANNELS or pre_skip != PRE_SKIP or sample_rate != SAMPLE_RATE or mapping_family != 0:
        raise ToolError("FFmpeg produced an Opus profile incompatible with Touhou 6 New Classic.")
    audio_packets = packets[2:]
    wrong_sizes = sorted({len(packet) for packet in audio_packets if len(packet) != PACKET_BYTES})
    if wrong_sizes:
        raise ToolError(f"FFmpeg did not produce the required fixed-size Nintendo Opus packets: {wrong_sizes}")
    framed = bytearray()
    for packet in audio_packets:
        framed.extend(struct.pack(">I", len(packet)))
        framed.extend(struct.pack("<I", 1))
        framed.extend(packet)
    header = bytearray()
    header.extend(struct.pack("<I", BASIC_INFO_ID))
    header.extend(struct.pack("<I", 0x18))
    header.extend(struct.pack("<B", 0))
    header.extend(struct.pack("<B", CHANNELS))
    header.extend(struct.pack("<H", FRAME_BLOCK_BYTES))
    header.extend(struct.pack("<I", SAMPLE_RATE))
    header.extend(struct.pack("<I", 0x20))
    header.extend(struct.pack("<I", 0))
    header.extend(struct.pack("<I", 0))
    header.extend(struct.pack("<H", PRE_SKIP))
    header.extend(struct.pack("<H", 0))
    output.write_bytes(header + struct.pack("<II", DATA_INFO_ID, len(framed)) + framed)
    frame_count = len(audio_packets)
    packet_samples = frame_count * 960 - PRE_SKIP
    exact_samples = final_granule - PRE_SKIP
    if exact_samples <= 0 or exact_samples > packet_samples:
        raise ToolError("Invalid final Opus duration produced by FFmpeg.")
    return frame_count, exact_samples, packet_samples, exact_samples / SAMPLE_RATE, output.stat().st_size


def convert(source: Path, output: Path) -> tuple[int, int, int, float, int]:
    source = source.expanduser().resolve()
    output = output.expanduser().resolve()
    if not source.is_file():
        raise ToolError(f"Input file does not exist: {source}")
    if source == output:
        raise ToolError("Input and output paths must be different.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="th06nc_nxopus_") as temp_dir:
        ogg = Path(temp_dir) / "encoded.opus"
        _encode_to_ogg(source, ogg)
        return _build_nintendo_opus(ogg, output)
