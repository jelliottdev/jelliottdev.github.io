"""Plot non-rune text differences per LP2 page from the transcription audit."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "exports/seventh-onion-transcription-variants.json"
OUTPUT = ROOT / "exports/figures/seventh-onion-transcription-variants.svg"


def draw():
    pages = json.loads(SOURCE.read_text(encoding="utf-8"))["pages"]
    if len(pages) != 58:
        raise ValueError("Expected 58 LP2 pages")
    left, right, top, bottom = 58, 884, 43, 229
    bar = (right - left) / 58
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 950 306" role="img" aria-labelledby="title desc">',
        '<title id="title">Non-rune transcription differences across LP2</title>',
        '<desc id="desc">The rune order matches on all 58 pages. Twenty-six pages have differences between runes or in other non-rune text. Pages 49 to 51 also contain five disputed alphanumeric grid cells.</desc>',
        '<rect width="950" height="306" fill="#fff"/>',
        '<text x="58" y="21" fill="#222" font-family="Arial,sans-serif" font-size="14" font-weight="bold">Changed gaps between runes, by page</text>',
    ]
    for count in range(6):
        y = bottom - count * 34
        lines.append(f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" stroke="#d8dee2"/>')
        lines.append(f'<text x="48" y="{y+4}" text-anchor="end" fill="#5c6670" font-family="Arial,sans-serif" font-size="11">{count}</text>')
    for index, page in enumerate(pages):
        x = left + index * bar + bar / 2
        count = page["non_rune_boundary_changes"]
        if count:
            lines.append(f'<rect x="{x-4:.1f}" y="{bottom-count*34}" width="8" height="{count*34}" fill="#2d667f"/>')
        else:
            lines.append(f'<circle cx="{x:.1f}" cy="{bottom-2}" r="2.6" fill="#88939a"/>')
        if page["grid_token_changes"]:
            lines.append(f'<circle cx="{x:.1f}" cy="34" r="4" fill="#a75c35"/>')
    for index in list(range(0, 58, 5)) + [57]:
        x = left + index * bar + bar / 2
        lines.append(f'<text x="{x:.1f}" y="248" text-anchor="middle" fill="#5c6670" font-family="Arial,sans-serif" font-size="10">{index}</text>')
    lines.extend([
        '<text x="471" y="267" text-anchor="middle" fill="#39434b" font-family="Arial,sans-serif" font-size="11">LP2 page index</text>',
        '<rect x="62" y="286" width="8" height="8" fill="#2d667f"/><text x="77" y="295" fill="#39434b" font-family="Arial,sans-serif" font-size="11">Non-rune text differs</text>',
        '<circle cx="267" cy="290" r="4" fill="#a75c35"/><text x="278" y="295" fill="#39434b" font-family="Arial,sans-serif" font-size="11">Grid cell differs</text>',
        '</svg>',
    ])
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    draw()
