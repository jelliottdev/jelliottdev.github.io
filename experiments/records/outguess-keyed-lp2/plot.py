"""Render a compact, phone-width view of unverified keyed retrieval counts."""
from collections import Counter
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
report = json.loads((HERE/'results.json').read_text(encoding='utf8'))
keys = json.loads((HERE/'plan.json').read_text(encoding='utf8'))['keys']
parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 444" role="img" aria-labelledby="title desc">',
    '<title id="title">Keyed OutGuess retrievals on 58 LP2 images</title>',
    '<desc id="desc">Count of nonempty outputs for each of six keys; none is authenticated as a message.</desc>',
    '<rect width="320" height="444" fill="#f3f4f6"/>',
    '<text x="16" y="29" font-family="Arial,sans-serif" font-size="17" font-weight="700" fill="#263238">Nonempty outputs by key</text>',
    '<text x="16" y="51" font-family="Arial,sans-serif" font-size="13" fill="#52606a">Original LP2 JPEGs · 58 images per key</text>'
]
for index, key in enumerate(keys):
    y = 83 + 53*index
    rows = [r for r in report['rows'] if r['key']==key]
    count = sum(r['status']=='output-unverified' for r in rows)
    parts += [
        f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="13" font-weight="600" fill="#263238">{html.escape(key)}</text>',
        f'<rect x="16" y="{y+10}" width="244" height="14" fill="#dce1e4"/>',
        f'<rect x="16" y="{y+10}" width="{round(244*count/58,2)}" height="14" fill="#355f75"/>',
        f'<text x="268" y="{y+22}" font-family="Arial,sans-serif" font-size="13" fill="#263238">{count}/58</text>'
    ]
parts += [
    '<line x1="16" y1="397" x2="304" y2="397" stroke="#c4ccd1"/>',
    '<text x="16" y="419" font-family="Arial,sans-serif" font-size="13" fill="#35434a">A bar means bytes were returned.</text>',
    '<text x="16" y="436" font-family="Arial,sans-serif" font-size="13" fill="#35434a">It does not identify a message.</text>',
    '</svg>'
]
(HERE/'figure.svg').write_text('\n'.join(parts)+'\n',encoding='utf8',newline='\n')
