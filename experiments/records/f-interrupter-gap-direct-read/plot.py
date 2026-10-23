"""Draw mapped and unmapped within-page F gaps for four literal GP readings."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
names = {
    ('position-distance', 'zero-based-index-0-to-28'): 'Distance → index',
    ('position-distance', 'exact-GP-prime-value'): 'Distance → prime',
    ('intervening-rune-count', 'zero-based-index-0-to-28'): 'Between → index',
    ('intervening-rune-count', 'exact-GP-prime-value'): 'Between → prime',
}
cases = [item for item in result['cases'] if item['boundary'] == 'within-page-only']
assert len(cases) == 4 and all(item['gap_count'] == 403 for item in cases)
parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 330" role="img" aria-labelledby="title desc">',
    '<title id="title">Direct readings of F gaps on LP2 pages</title>',
    '<desc id="desc">Of 403 within-page consecutive F gaps, the four direct interpretations map 273, 157, 281, and 140 values, respectively. Every interpretation leaves gaps unmapped, so each needs another rule to form a complete symbol stream.</desc>',
    '<rect width="340" height="330" fill="#fff"/>',
    '<text x="16" y="30" font-family="sans-serif" font-size="18" fill="#202b32">Can every F gap be one rune?</text>',
    '<text x="16" y="53" font-family="sans-serif" font-size="13" fill="#52616a">403 within-page gaps · no values skipped</text>',
]
for i, case in enumerate(cases):
    y = 75 + i*55
    name = names[(case['gap_rule'], case['value_map'])]
    mapped = case['mapped_count']
    bar = round(308*mapped/403)
    parts += [
        f'<text x="16" y="{y+13}" font-family="sans-serif" font-size="14" fill="#202b32">{name}</text>',
        f'<text x="252" y="{y+13}" font-family="sans-serif" font-size="14" fill="#365d71">{mapped} / 403</text>',
        f'<rect x="16" y="{y+21}" width="308" height="14" fill="#d9dfe3"/>',
        f'<rect x="16" y="{y+21}" width="{bar}" height="14" fill="#35637c"/>',
    ]
parts += [
    '<path d="M16 299H324" stroke="#c7d0d5"/>',
    '<text x="16" y="319" font-family="sans-serif" font-size="13" fill="#52616a">Gray gaps need an additional encoding rule.</text>',
    '</svg>',
]
(HERE / 'gaps.svg').write_text('\n'.join(parts) + '\n', encoding='utf-8', newline='\n')
print('Wrote gaps.svg')
