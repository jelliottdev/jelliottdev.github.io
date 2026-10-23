"""Draw the exact block boundaries and comparison counts for this bounded test."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def make() -> None:
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["payload_bytes"] == 256
    assert result["unique_candidate_bytes"] == 324
    assert result["comparisons"] == 16848 and not result["matches"]
    widths = (16, 32, 64)
    labels = {
        16: ("MD5", "5,184 comparisons"),
        32: ("SHA-256 · SHA3-256 · BLAKE2s", "7,776 comparisons"),
        64: ("SHA-512 · SHA3-512 · BLAKE2b", "3,888 comparisons"),
    }
    pieces = []
    for size, y in zip(widths, (116, 207, 298)):
        count = 256 // size
        label, total = labels[size]
        assert result["aligned_blocks_by_size"][str(size)] == count
        pieces.append(f'<text x="20" y="{y-31}" class="rowhead">{size}-byte blocks · {count} positions</text>')
        for index in range(count):
            x = 20 + index * (320 / count)
            cell = 320 / count
            shade = "#dce7ed" if index % 2 == 0 else "#eff3f5"
            pieces.append(f'<rect x="{x:.2f}" y="{y-20}" width="{cell:.2f}" height="25" '
                          f'fill="{shade}" stroke="#9fb1bb" stroke-width="1"/>')
        pieces.append(f'<text x="20" y="{y+27}" class="rowmeta">{label}</text>')
        pieces.append(f'<text x="340" y="{y+44}" text-anchor="end" class="rowmeta">{total}</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 360 390">
<title id="title">Aligned digest block search of the 256-byte LP2 grid payload</title>
<desc id="desc">The payload is divided from byte zero into 16 MD5-sized blocks, eight 256-bit hash-sized blocks, and four 512-bit hash-sized blocks. There were 16,848 exact comparisons of 324 unique candidate inputs and no matches.</desc>
<style>text{{font-family:Arial,Helvetica,sans-serif;fill:#26343e}}.rowhead{{font-size:15px;font-weight:700}}.rowmeta{{font-size:12px}}.sub{{font-size:13px;fill:#536773}}</style>
<rect width="360" height="390" fill="#fff"/>
<text x="20" y="29" font-size="19" font-weight="700">One payload, three block sizes</text>
<text x="20" y="52" class="sub">324 inputs · 7 hashes · 16,848 checks</text>
<text x="20" y="70" class="sub">No complete aligned block matched a digest.</text>
{''.join(pieces)}
<line x1="20" y1="361" x2="340" y2="361" stroke="#c9d3d8"/>
<text x="20" y="381" class="sub">Byte 0 origin · no sliding windows or padding</text>
</svg>'''
    (HERE / "blocks.svg").write_text(svg + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    make()
