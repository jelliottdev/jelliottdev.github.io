"""Draw the three within-page breaks used by the section-count audit."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "exports/figures/section-rune-splits.svg"


def draw():
    report = json.loads((ROOT / "exports/section-rune-counts.json").read_text(encoding="utf-8"))
    rows = [
        ("LP1-16", "Instruction", "KT2"),
        ("LP2-33", "WT 3 dots", "Cuneiform"),
        ("LP2-39", "Cuneiform", "Cunieform 3 dots"),
    ]
    by_section = {row["section"]: row for row in report["sections"]}
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 210" role="img" aria-labelledby="title desc">',
             '<title id="title">Within-page section breaks</title>',
             '<desc id="desc">The three pages whose rune streams split at a section mark: LP1-16 at 82 of 89 runes, LP2-33 at 91 of 214, and LP2-39 at 119 of 240.</desc>',
             '<rect width="420" height="210" fill="#fff"/>']
    for index, (page, first, second) in enumerate(rows):
        left = next(span["runes"] for span in by_section[first]["spans"]
                    if span["page"].upper() == page)
        right = next(span["runes"] for span in by_section[second]["spans"]
                     if span["page"].upper() == page)
        y = 12 + index * 68
        cut = round(310 * left / (left + right), 2)
        lines.extend([f'<text x="8" y="{y+14}" font-family="system-ui,sans-serif" font-size="13" fill="#202b31">{page}</text>',
                      f'<rect x="96" y="{y}" width="310" height="18" fill="#d9e2e6"/>',
                      f'<rect x="96" y="{y}" width="{cut}" height="18" fill="#35596b"/>',
                      f'<path d="M {96+cut} {y-3} V {y+22}" stroke="#17262e" stroke-width="1.5"/>',
                      f'<text x="96" y="{y+39}" font-family="system-ui,sans-serif" font-size="11" fill="#35454d">{first}: {left}</text>',
                      f'<text x="406" y="{y+39}" text-anchor="end" font-family="system-ui,sans-serif" font-size="11" fill="#35454d">{second}: {right}</text>'])
    lines.append('</svg>')
    return ('\n'.join(lines) + '\n').encode('utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = draw()
    if args.check:
        assert TARGET.read_bytes() == result
        print('PASS: three section-boundary bars match the audited rune counts')
    else:
        TARGET.write_bytes(result)
        print(TARGET.relative_to(ROOT))
