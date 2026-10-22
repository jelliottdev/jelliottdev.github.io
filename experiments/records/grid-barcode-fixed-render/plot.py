"""Render source bit canvases with the fixed detector outcome."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ROWS = json.loads((ROOT / "exports/grid-binary-audit.json").read_text(encoding="utf-8"))["bit_rows"]
REPORT = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
TARGET = HERE / "bit-canvases.svg"


def picture():
    groups = [("All three pages · 64 × 32", ROWS),
              ("LP2-49 · 64 × 10", ROWS[:10]),
              ("LP2-50 · 64 × 13", ROWS[10:23]),
              ("LP2-51 · 64 × 9", ROWS[23:])]
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 690 470" role="img" aria-labelledby="title desc">',
           '<title id="title">Four fixed grid bit canvases</title>',
           '<desc id="desc">The 64-bit-wide manuscript rows are shown as a full 32-row grid and three page-only groups. QR Code and Data Matrix decoders return no valid payload for any of the 16 declared transformations of each canvas.</desc>',
           '<rect width="690" height="470" fill="#faf9f5"/>',
           '<g font-family="Arial, sans-serif" fill="#26353d">',
           '<text x="20" y="30" font-size="19" font-weight="bold">Grid bits at manuscript row width</text>',
           '<text x="20" y="49" font-size="12">Eight fixed bits per token · eight tokens per row · no reflow</text>']
    slots = [(20, 70), (354, 70), (20, 265), (354, 265)]
    for (label, rows), (left, top), result in zip(groups, slots, REPORT["canvases"]):
        out += [f'<rect x="{left}" y="{top}" width="316" height="180" fill="#fff" stroke="#c9d0d1"/>',
                f'<text x="{left + 12}" y="{top + 22}" font-size="13" font-weight="bold">{label}</text>',
                f'<text x="{left + 12}" y="{top + 165}" font-size="11">{sum(bool(c["decoded"]) for c in result["variants"])} valid decodes / 16 transforms</text>',
                '<g fill="#283b45" shape-rendering="crispEdges">']
        unit = 3.7
        for y, row in enumerate(rows):
            for x, bit in enumerate(row):
                if bit == "1":
                    out.append(f'<rect x="{left + 12 + x * unit:.1f}" y="{top + 32 + y * unit:.1f}" width="{unit:.1f}" height="{unit:.1f}"/>')
        out.append('</g>')
    out += ['<text x="20" y="457" font-size="11">Positive QR and Data Matrix controls decoded. Blank space in each card is presentation only.</text>', '</g>', '</svg>']
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    rendered = picture()
    if args.check:
        assert TARGET.read_text(encoding="utf-8") == rendered
        print("PASS: exact source-bit SVG")
    else:
        TARGET.write_text(rendered, encoding="utf-8", newline="\n")
        print(TARGET)
