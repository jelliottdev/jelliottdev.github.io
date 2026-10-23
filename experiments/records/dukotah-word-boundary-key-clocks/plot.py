"""Render and check a phone-width summary of whole-search controls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render(data):
    rows = [("Separator clock", "FH1"), ("Punctuation reset", "FH3"), ("Word prime sums", "word_sums")]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="360" height="322" viewBox="0 0 360 322" role="img" aria-labelledby="title desc">',
        '<title id="title">Boundary-key methods against shuffled searches</title>',
        '<desc id="desc">For each method, the number of 49 whole-search shuffled controls reaching or exceeding the manuscript best. The source known-page result matched only 56 of 85 rune positions.</desc>',
        '<rect width="360" height="322" fill="#f7f8fa"/>',
        '<text x="16" y="27" font-family="Arial,sans-serif" font-size="17" font-weight="700" fill="#202a33">Did a manuscript score stand out?</text>',
        '<text x="16" y="51" font-family="Arial,sans-serif" font-size="13" fill="#45535f">Shuffles at least as high as the real best</text>',
    ]
    for index, (label, key) in enumerate(rows):
        count = data['null_at_least_observed'][key]
        y = 81 + index * 63
        width = round(224 * count / 49, 2)
        parts.extend([
            f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="14" font-weight="600" fill="#202a33">{label}</text>',
            f'<rect x="16" y="{y+10}" width="224" height="15" rx="3" fill="#dbe2e7"/>',
            f'<rect x="16" y="{y+10}" width="{width}" height="15" rx="3" fill="#3e647d"/>',
            f'<text x="252" y="{y+23}" font-family="Arial,sans-serif" font-size="14" fill="#202a33">{count} / 49</text>',
        ])
    parts.extend([
        '<path d="M16 255 H344" stroke="#cbd4db"/>',
        '<text x="16" y="279" font-family="Arial,sans-serif" font-size="14" font-weight="600" fill="#202a33">Known-page check: 56 / 85 runes</text>',
        '<text x="16" y="301" font-family="Arial,sans-serif" font-size="13" fill="#45535f">Matching opening, then diverges; no full recovery.</text>',
        '</svg>',
    ])
    return '\n'.join(parts) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    output = render(data)
    path = HERE / 'comparison.svg'
    if args.check:
        assert path.read_text(encoding='utf-8') == output
        assert data['known_page_diagnostic']['matched_rune_positions'] == 56
        print('PASS chart matches saved counts')
    else:
        path.write_text(output, encoding='utf-8', newline='\n')
        print(path)
