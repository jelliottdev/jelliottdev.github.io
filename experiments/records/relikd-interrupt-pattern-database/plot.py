"""Compact, mobile-readable known-period control figure."""

import argparse
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "control-results.json").read_text(encoding="utf8"))
GROUPS = [
    ("Mirror pattern", "mirror", 4),
    ("Remove F, then split", "modulo_a", 10),
    ("Split, then remove F", "modulo_b", 10),
]


def build():
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 276" role="img" aria-labelledby="title desc">',
             '<title id="title">Known-text period detection in three source methods</title>',
             '<desc id="desc">The correct period ranks first in four of four mirror, ten of ten remove-then-split, and eight of ten split-then-remove controls. Every saved LP2 score was also recounted, but these controls do not decode LP2.</desc>',
             '<rect width="320" height="276" fill="#f5f7f8"/>',
             '<g font-family="Arial, sans-serif" fill="#263843">',
             '<text x="16" y="29" font-size="17" font-weight="700">Does the known period stand out?</text>',
             '<text x="16" y="50" font-size="12.5" fill="#52646f">Period 5 planted in 600 known runes</text>']
    for index, (label, family, total) in enumerate(GROUPS):
        y = 87 + index * 55
        found = sum(x["true_period_strict_winner"] for x in DATA["rows"] if x["family"] == family)
        assert len([x for x in DATA["rows"] if x["family"] == family]) == total
        lines += [f'<text x="16" y="{y}" font-size="13.5" font-weight="600">{html.escape(label)}</text>',
                  f'<rect x="16" y="{y+10}" width="230" height="10" rx="2" fill="#cdd5d9"/>',
                  f'<rect x="16" y="{y+10}" width="{230*found/total:.1f}" height="10" rx="2" fill="#315d77"/>',
                  f'<text x="258" y="{y+19}" font-size="14" font-weight="700">{found}/{total}</text>']
    lines += ['<path d="M16 244H304" stroke="#cdd5d9"/>',
              '<text x="16" y="263" font-size="12.5" fill="#52646f">Saved LP2 scores checked: 7,407</text>',
              '</g></svg>']
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = HERE / "control.svg"
    output = build()
    if args.check:
        assert path.read_text(encoding="utf8") == output
    else:
        path.write_text(output, encoding="utf8", newline="\n")
    print("known-period control plot", len(output), "characters")
