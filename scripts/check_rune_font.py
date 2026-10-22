#!/usr/bin/env python3
"""Check the locally served Runic font against manuscript transcription characters."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from struct import unpack_from


ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "fonts/NotoSansRunic-Regular.ttf"
LICENSE = ROOT / "fonts/OFL-NotoSansRunic.txt"
EXPECTED_SHA256 = "615b6c1166a8c51816dc1536784acbf486547e3bed03dbfdd70910e10066793b"


def u16(data: bytes, pos: int) -> int:
    return unpack_from(">H", data, pos)[0]


def i16(data: bytes, pos: int) -> int:
    return unpack_from(">h", data, pos)[0]


def u32(data: bytes, pos: int) -> int:
    return unpack_from(">I", data, pos)[0]


def glyph_for(codepoint: int, data: bytes, cmap: int) -> int:
    """Read a BMP codepoint from the font's format-4 Unicode cmap."""
    count = u16(data, cmap + 2)
    for record in range(count):
        entry = cmap + 4 + record * 8
        platform, encoding = u16(data, entry), u16(data, entry + 2)
        subtable = cmap + u32(data, entry + 4)
        if (platform, encoding) not in ((0, 3), (3, 1)) or u16(data, subtable) != 4:
            continue
        segments = u16(data, subtable + 6) // 2
        ends = subtable + 14
        starts = ends + segments * 2 + 2
        deltas = starts + segments * 2
        offsets = deltas + segments * 2
        for index in range(segments):
            if codepoint > u16(data, ends + index * 2):
                continue
            if codepoint < u16(data, starts + index * 2):
                break
            delta = i16(data, deltas + index * 2)
            range_offset = u16(data, offsets + index * 2)
            if not range_offset:
                return (codepoint + delta) & 0xFFFF
            slot = offsets + index * 2 + range_offset
            glyph = u16(data, slot + 2 * (codepoint - u16(data, starts + index * 2)))
            return (glyph + delta) & 0xFFFF if glyph else 0
    return 0


def main() -> None:
    data = FONT.read_bytes()
    assert hashlib.sha256(data).hexdigest() == EXPECTED_SHA256, "font differs from pinned upstream copy"
    tables = {
        data[12 + i * 16 : 16 + i * 16].decode("ascii"): u32(data, 12 + i * 16 + 8)
        for i in range(u16(data, 4))
    }
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    alphabet = {ord(item["rune"]) for item in index["alphabet"]}
    transcription = json.dumps(index["pages"], ensure_ascii=False)
    runes = {ord(char) for char in transcription if 0x16A0 <= ord(char) <= 0x16FF}
    missing = sorted(cp for cp in alphabet | runes if glyph_for(cp, data, tables["cmap"]) == 0)
    assert not missing, f"missing glyphs: {', '.join(f'U+{cp:04X}' for cp in missing)}"
    assert len(alphabet) == 29, f"expected 29 Gematria Primus characters, found {len(alphabet)}"
    license_text = LICENSE.read_text(encoding="utf-8")
    assert "SIL OPEN FONT LICENSE Version 1.1" in license_text
    css = (ROOT / "style.css").read_text(encoding="utf-8")
    assert 'url("fonts/NotoSansRunic-Regular.ttf")' in css
    assert "unicode-range:U+16A0-16FF" in css
    print(f"Rune font coverage OK: {len(alphabet)} alphabet glyphs, {len(runes)} transcription glyphs")


if __name__ == "__main__":
    main()
