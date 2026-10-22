"""Draw byte-size differences between the archived and hosted LP2 JPEG versions."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "exports/cicada-2014-seventh-onion.json"
OUTPUT = ROOT / "exports/figures/seventh-onion-jpeg-versions.svg"


def draw():
    pages = json.loads(REPORT.read_text(encoding="utf-8"))["pages"]
    if len(pages) != 58:
        raise ValueError("Expected all 58 LP2 pages")
    left, right, top, bottom = 68, 880, 34, 246
    scale = (bottom - top) / 30000
    width = (right - left) / 58
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 950 320" role="img" aria-labelledby="title desc">',
        '<title id="title">File-size difference across the 58 LP2 JPEG pairs</title>',
        '<desc id="desc">Thirty-five pairs differ by an 18-byte JFIF header only. The other twenty-three pairs differ by roughly 17,000 to 29,000 bytes and have different JPEG image data.</desc>',
        '<rect width="950" height="320" fill="#fff"/>',
        '<text x="68" y="20" fill="#222" font-family="Arial,sans-serif" font-size="14" font-weight="bold">Extra bytes in the hosted page file</text>',
    ]
    for value in (0, 10000, 20000, 30000):
        y = bottom - value * scale
        lines.extend([
            f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#d8dee2" stroke-width="1"/>',
            f'<text x="59" y="{y+4:.1f}" text-anchor="end" fill="#5c6670" font-family="Arial,sans-serif" font-size="11">{value//1000}k</text>',
        ])
    for i, page in enumerate(pages):
        x = left + i * width + width / 2
        delta = page["byte_difference"]
        if page["relationship"] == "hosted-adds-18-byte-JFIF":
            lines.append(f'<circle cx="{x:.1f}" cy="{bottom-2}" r="3.1" fill="#667783"/>')
        else:
            height = delta * scale
            lines.append(f'<rect x="{x-4:.1f}" y="{bottom-height:.1f}" width="8" height="{height:.1f}" fill="#2d667f"/>')
    for i in list(range(0, 58, 5)) + [57]:
        x = left + i * width + width / 2
        lines.append(f'<text x="{x:.1f}" y="265" text-anchor="middle" fill="#5c6670" font-family="Arial,sans-serif" font-size="10">{i}</text>')
    lines.extend([
        '<text x="472" y="284" text-anchor="middle" fill="#39434b" font-family="Arial,sans-serif" font-size="11">LP2 page index</text>',
        '<circle cx="75" cy="305" r="3.1" fill="#667783"/><text x="86" y="309" fill="#39434b" font-family="Arial,sans-serif" font-size="11">JFIF header only (35)</text>',
        '<rect x="275" y="300" width="8" height="8" fill="#2d667f"/><text x="290" y="309" fill="#39434b" font-family="Arial,sans-serif" font-size="11">Different JPEG image data (23)</text>',
        '</svg>',
    ])
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    draw()
