"""Render the four fixed 16-byte target blocks as an accessible SVG."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 315" role="img" aria-labelledby="title desc">',
    '<title id="title">Four printed LP2-56 target blocks</title>',
    '<desc id="desc">The 64 printed bytes split into four consecutive 16-byte blocks. None equals the MD5 digest of any of the 324 unique preserved-artifact candidate byte strings.</desc>',
    '<rect width="720" height="315" fill="#fff"/>',
    '<text x="24" y="35" fill="#202b32" font-family="sans-serif" font-size="20">LP2-56: four 16-byte blocks</text>',
    '<text x="24" y="58" fill="#52616a" font-family="sans-serif" font-size="13">Exact MD5 comparison · 324 candidate byte strings per block</text>',
]
for i, block in enumerate(data['blocks']):
    y = 78 + i * 56
    parts += [
        f'<rect x="24" y="{y}" width="672" height="45" fill="#edf0f2" stroke="#c7d0d5"/>',
        f'<text x="38" y="{y+19}" fill="#202b32" font-family="sans-serif" font-size="14" font-weight="bold">Block {i+1} · bytes {16*i}–{16*i+15}</text>',
        f'<text x="38" y="{y+37}" fill="#485a64" font-family="monospace" font-size="13">{block["hex"]}</text>',
        f'<text x="642" y="{y+28}" fill="#355c70" font-family="sans-serif" font-size="16" font-weight="bold">{len(block["matches"])} hits</text>',
    ]
parts.append('</svg>')
(HERE / 'blocks.svg').write_text('\n'.join(parts) + '\n', encoding='utf-8', newline='\n')
print('Wrote blocks.svg')
