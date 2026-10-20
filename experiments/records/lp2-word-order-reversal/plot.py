"""Export actual LP2-31 source positions and the per-page case summary."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
page = next(p for p in result['pages'] if p['page'] == 'lp2-31')
parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 420" role="img" aria-labelledby="title desc">',
    '<title id="title">Reversed segment order: LP2-31 source positions</title>',
    '<desc id="desc">First six output positions for each boundary convention. Both start with source runes 266, 267, 268, 258, 259, 260, counted from zero.</desc>',
    '<rect width="360" height="420" fill="#faf9f5"/><g fill="#243c48" font-family="sans-serif">',
    '<text x="18" y="30" font-size="18">LP2-31: read the last segment first</text>',
    '<text x="18" y="57" font-size="14">Source rune ordinal at each output position</text>',
    '<text x="18" y="94" font-size="14">Output</text>',
    '<text x="115" y="94" font-size="14">Split lines</text>',
    '<text x="232" y="94" font-size="14">Join lines</text>',
]
for i in range(6):
    y = 127 + i * 32
    values = [case['source_ordinals'][i] for case in page['cases']]
    parts.append(f'<path d="M18 {y+10} H342" stroke="#dce0df"/>'
                 f'<text x="18" y="{y}" font-size="17">{i}</text>'
                 f'<text x="115" y="{y}" font-size="17">{values[0]}</text>'
                 f'<text x="232" y="{y}" font-size="17">{values[1]}</text>')
parts.extend([
    '<text x="18" y="330" font-size="14">266 → 267 → 268: keep the segment forward.</text>',
    '<text x="18" y="356" font-size="14">Then jump back to the preceding segment.</text>',
    '<text x="18" y="382" font-size="14">Positions count from zero; not plaintext.</text>',
    '<text x="18" y="405" font-size="14">The full outputs differ later in the page.</text></g></svg>\n',
])
(HERE / 'source-trace.svg').write_text(''.join(parts), encoding='utf-8', newline='\n')
with (HERE / 'page-summary.csv').open('w', encoding='utf-8', newline='') as stream:
    writer = csv.DictWriter(stream, lineterminator='\n', fieldnames=[
        'page', 'runes', 'cases', 'distinct_outputs', 'opening_comparisons', 'matching_cases'])
    writer.writeheader()
    for page in result['pages']:
        writer.writerow({
            'page': page['page'], 'runes': page['rune_count'], 'cases': len(page['cases']),
            'distinct_outputs': len({tuple(c['output_indices']) for c in page['cases']}),
            'opening_comparisons': len(page['cases']) * 9,
            'matching_cases': sum(bool(c['matching_openings']) for c in page['cases']),
        })
