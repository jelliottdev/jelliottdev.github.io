"""Draw the finite square-length census, without implying a chance probability."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
rows = [('Runes', 'runes'), ('GP prime digits', 'prime_digits'),
        ('Index digits, 0-based', 'index_0_digits'), ('Index digits, 1-based', 'index_1_digits')]
maximum = max(RESULT['perfect_square_intervals'][key]['count'] for _, key in rows)
parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 310" role="img" aria-labelledby="title desc">',
    '<title id="title">Perfect-square lengths among all contiguous page ranges</title>',
    '<desc id="desc">Of 820 contiguous LP2-00 through LP2-39 page intervals, 11 have square rune counts, 8 square GP-prime decimal digit counts, 3 square zero-based index digit counts and 4 square one-based index digit counts.</desc>',
    '<rect width="720" height="310" fill="#fff"/>',
    '<text x="20" y="35" font-family="sans-serif" font-size="20" fill="#202b32">Square lengths across 820 page intervals</text>',
    '<text x="20" y="58" font-family="sans-serif" font-size="13" fill="#53616a">These intervals overlap; counts are descriptive, not probabilities.</text>',
]
for i, (label, key) in enumerate(rows):
    count = RESULT['perfect_square_intervals'][key]['count']
    y = 91 + i * 52
    width = int(360 * count / maximum)
    parts += [
        f'<text x="20" y="{y+16}" font-family="sans-serif" font-size="15" fill="#202b32">{label}</text>',
        f'<rect x="246" y="{y}" width="360" height="24" fill="#edf0f2"/>',
        f'<rect x="246" y="{y}" width="{width}" height="24" fill="#325e75"/>',
        f'<text x="620" y="{y+17}" font-family="sans-serif" font-size="16" fill="#202b32">{count}</text>',
    ]
parts.append('</svg>')
(HERE / 'squares.svg').write_text('\n'.join(parts) + '\n', encoding='utf-8', newline='\n')
print('Wrote squares.svg')
