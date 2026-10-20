"""Show the first actual boundary-dependent output positions for LP2-31."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
page = next(page for page in result["pages"] if page["page"] == "lp2-31")
split, joined = page["cases"]
first = next(i for i, (a, b) in enumerate(zip(split["source_ordinals"], joined["source_ordinals"])) if a != b)
parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 370" role="img" aria-labelledby="title desc">',
    '<title id="title">Where line-boundary rules first change LP2-31 output</title>',
    '<desc id="desc">Six consecutive output positions from the saved result, starting at the first difference. Values are original source rune ordinals, counted from zero.</desc>',
    '<rect width="360" height="370" fill="#faf9f5"/>',
    '<g fill="#243c48" font-family="sans-serif">',
    '<text x="18" y="28" font-size="19">LP2-31: two boundary rules</text>',
    '<text x="18" y="53" font-size="13">Source rune ordinal at each output position</text>',
    '<text x="18" y="88" font-size="13">Output</text>',
    '<text x="108" y="88" font-size="13">Split lines</text>',
    '<text x="233" y="88" font-size="13">Join lines</text>',
]
for row, i in enumerate(range(first, first + 6)):
    y = 119 + row * 30
    parts.append(f'<path d="M18 {y+9} H340" stroke="#dce0df"/><text x="18" y="{y}" font-size="16">{i}</text><text x="108" y="{y}" font-size="16">{split["source_ordinals"][i]}</text><text x="233" y="{y}" font-size="16">{joined["source_ordinals"][i]}</text>')
parts.extend([
    '<text x="18" y="310" font-size="13">All positions count from zero.</text>',
    '<text x="18" y="333" font-size="13">Both routes retain every rune exactly once.</text>',
    '<text x="18" y="356" font-size="13">These are positions, not decoded words.</text></g></svg>\n',
])
(HERE / "boundary-trace.svg").write_text("".join(parts), encoding="utf-8", newline="\n")
