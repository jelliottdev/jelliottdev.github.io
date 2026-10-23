"""Generate compact responsive SVG from exact result counts."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))['rows']
out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 310" role="img" aria-labelledby="t d">',
       '<title id="t">Dictionary pattern matches by word length</title>',
       '<desc id="d">LP2 cipher and random-control affine match percentages are similar at every length; ordinary Caesar matches fall near zero by length six.</desc>',
       '<style>text{font-family:Arial,sans-serif;fill:#27333b;font-size:15px}.head{font-weight:700;font-size:17px}.small{font-size:15px;fill:#51616b}</style>',
       '<rect width="340" height="310" fill="#f5f7f8"/>',
       '<text class="head" x="16" y="25">Word patterns in the pinned corpus</text>',
       '<text class="small" x="16" y="45">Affine match rate · LP2 vs random rune words</text>']
for j, r in enumerate(rows):
    y = 76 + 43*j
    c = 100*r['affine_hits']/r['cipher_words']
    n = 100*r['random_affine_hits']/r['random_n']
    out.extend([f'<text x="16" y="{y+10}">{r["length"]} runes</text>',
                f'<rect x="100" y="{y-4}" width="{180*c/100:.2f}" height="13" fill="#315d79"/>',
                f'<rect x="100" y="{y+12}" width="{180*n/100:.2f}" height="8" fill="#8a9fae"/>',
                f'<text x="287" y="{y+9}">{c:.1f}%</text>'])
out.extend(['<rect x="17" y="285" width="12" height="9" fill="#315d79"/><text class="small" x="36" y="294">LP2</text>',
            '<rect x="97" y="285" width="12" height="9" fill="#8a9fae"/><text class="small" x="116" y="294">uniform-random control</text>',
            '</svg>'])
(HERE/'word-patterns.svg').write_text('\n'.join(out)+'\n',encoding='utf-8')
