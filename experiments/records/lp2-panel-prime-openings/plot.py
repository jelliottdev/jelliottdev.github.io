"""Draw the exact panel-derived prime cycle, with raw and modulo-29 values."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
key = result["key"]
assert len(key) == 16
parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 400" role="img" aria-labelledby="title desc">',
         '<title id="title">The sixteen LP2-15 panel-derived prime shifts</title>',
         '<desc id="desc">Spiral steps one to sixteen give primes ' + ', '.join(map(str, key)) + '. Each is reduced modulo 29 for the rune shift.</desc>',
         '<rect width="760" height="400" fill="#f6f6f2"/>',
         '<g font-family="Arial, sans-serif" fill="#253b47">',
         '<text x="25" y="38" font-size="23">LP2-15 spiral as a repeating shift stream</text>',
         '<text x="25" y="66" font-size="15">Step · selected prime · remainder modulo 29</text>']
for i, n in enumerate(key):
    x, y = 25 + (i % 8) * 90, 90 + (i // 8) * 128
    parts.extend([f'<rect x="{x}" y="{y}" width="80" height="105" fill="white" stroke="#cbd4d8"/>',
                  f'<text x="{x+40}" y="{y+23}" text-anchor="middle" font-size="15">{i+1}</text>',
                  f'<text x="{x+40}" y="{y+54}" text-anchor="middle" font-size="19" font-weight="bold">{n}</text>',
                  f'<text x="{x+40}" y="{y+83}" text-anchor="middle" font-size="21" fill="#275b72">{n % 29}</text>'])
parts.extend(['<text x="25" y="372" font-size="16">The sixteen steps repeat; offsets 0–15 cover every starting position.</text>',
              '</g></svg>'])
svg = "\n".join(parts) + "\n"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
path = HERE / "key-cycle.svg"
if args.check:
    assert path.read_text(encoding="utf-8") == svg
else:
    path.write_text(svg, encoding="utf-8", newline="\n")
print("PASS: panel prime cycle figure")
