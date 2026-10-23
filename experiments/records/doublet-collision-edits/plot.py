"""Compact, data-derived figure for the collision-edit result."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
rows = [
    ("Original LP2", 12956, 86, "#315d77"),
    ("Delete later copy", DATA["rules"]["delete_later"]["output_runes"], DATA["rules"]["delete_later"]["output_doublets"], "#4e7588"),
    ("Insert F", DATA["rules"]["insert_fixed_f"]["output_runes"], DATA["rules"]["insert_fixed_f"]["output_doublets"], "#718b98"),
    ("Insert other rune", DATA["rules"]["insert_nonmatching"]["output_runes"], DATA["rules"]["insert_nonmatching"]["output_doublets"], "#9eabb1"),
]
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="760" height="300" viewBox="0 0 760 300" role="img" aria-labelledby="title desc">',
       '<title id="title">Adjacent repeats after three fixed collision edits</title>',
       '<desc id="desc">Original LP2: 86 adjacent repeats across 12,956 runes. Delete later copy: zero repeats and 12,870 runes. Insert F: eight repeats and 13,042 runes. Insert a nonmatching rune: zero repeats and 13,042 runes.</desc>',
       '<rect width="760" height="300" fill="#f6f7f8"/>',
       '<text x="24" y="34" fill="#26343b" font-family="system-ui,sans-serif" font-size="19" font-weight="650">Adjacent equal runes after a forward edit</text>',
       '<text x="24" y="56" fill="#52616a" font-family="system-ui,sans-serif" font-size="13">Same LP2-00–55 input; each page edited separately</text>']
for i, (label, total, repeats, color) in enumerate(rows):
    y = 99 + i * 48
    bar = repeats / 86 * 300
    svg.extend([
        f'<text x="24" y="{y}" fill="#26343b" font-family="system-ui,sans-serif" font-size="15">{label}</text>',
        f'<rect x="214" y="{y-14}" width="300" height="17" fill="#e1e7ea"/>',
        f'<rect x="214" y="{y-14}" width="{bar:.2f}" height="17" fill="{color}"/>',
        f'<text x="526" y="{y}" fill="#26343b" font-family="system-ui,sans-serif" font-size="15" font-weight="650">{repeats}</text>',
        f'<text x="604" y="{y}" fill="#52616a" font-family="system-ui,sans-serif" font-size="14">{total:,} runes</text>',
    ])
svg += ['<text x="24" y="281" fill="#52616a" font-family="system-ui,sans-serif" font-size="12">These edits are controls; no LP2 plaintext or reverse-edit rule is supplied.</text>', '</svg>']
fresh = "\n".join(svg) + "\n"
path = HERE / "collision-edits.svg"
if "--check" in sys.argv:
    assert path.read_text(encoding="utf-8") == fresh
    print("Figure matches results")
else:
    path.write_text(fresh, encoding="utf-8", newline="\n")
    print(f"Wrote {path}")
