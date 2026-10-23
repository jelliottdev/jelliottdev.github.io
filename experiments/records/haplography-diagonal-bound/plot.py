"""Draw a responsive, text-labeled SVG from the measured bound."""
import json
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
r = json.loads((HERE/"results.json").read_text(encoding="utf-8"))
base = r["baseline"]["cv"]
free = r["sweep"][20]["free_diagonal_upper_cv"]
scale = 350 / .45
bars = [
    ("Observed; physical insertion", base, "#315c70", 0),
    ("20 freely placed additions", free, "#718b9a", 1),
    ("Autokey-signal bar", .4, "#1b303d", 2),
]
parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 510" role="img" aria-labelledby="title desc">',
    '<title id="title">Twenty duplicate-rune repairs cannot restore the tested autokey signature</title>',
    '<desc id="desc">Observed diagonal coefficient of variation is 0.061. Inserting physical duplicates leaves it unchanged. Even an artificial allowance to add 20 counts to any difference diagonal raises it only to 0.066, below the source autokey-signal bar of 0.40.</desc>',
    '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#1b303d}.heading{font-size:23px;font-weight:700}.label{font-size:18px}.number{font-size:19px;font-weight:700}.note{font-size:16px;fill:#50626b}.rule{stroke:#c9d1d5;stroke-width:1}</style>',
    '<rect width="600" height="510" fill="#fff"/>',
    '<text x="20" y="37" class="heading">A missed repeated rune</text>',
    '<text x="20" y="68" class="label">a → x → b</text><text x="185" y="68" class="note">insert a copy</text>',
    '<text x="20" y="102" class="label">a → x → x → b</text>',
    '<text x="20" y="133" class="note">Only the zero-difference count changes.</text>',
    '<text x="20" y="156" class="note">The other 28 difference counts are unchanged.</text>',
    '<line x1="20" x2="580" y1="177" y2="177" class="rule"/>',
    '<text x="20" y="216" class="heading">Unevenness of those 28 counts</text>',
]
for label, value, color, i in bars:
    y = 257 + 71*i
    parts.append(f'<text x="20" y="{y}" class="label">{escape(label)}</text>')
    parts.append(f'<rect x="20" y="{y+12}" width="{value*scale:.1f}" height="18" fill="{color}"/>')
    parts.append(f'<text x="{max(29+value*scale,110):.1f}" y="{y+28}" class="number">{value:.3f}</text>')
parts.extend([
    '<line x1="20" x2="370" y1="487" y2="487" class="rule"/>',
    '<text x="20" y="507" class="note">0</text><text x="331" y="507" class="note">0.45</text>',
    '</svg>'
])
(HERE/"diagonal-bound.svg").write_text("\n".join(parts)+"\n", encoding="utf-8")
