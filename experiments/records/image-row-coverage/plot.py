"""Render a compact count comparison from the preserved row report."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def render():
    report = json.loads((HERE/'results.json').read_bytes())
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 580" role="img" aria-labelledby="title desc">',
        '<title id="title">Individual rune rows matched on eight pages</title>',
        '<desc id="desc">43 of 65 reference rune rows matched. Seven pages have rune rows; LP2-50 is a non-runic control. These selected pages do not estimate whole-book accuracy.</desc>',
        '<rect width="380" height="580" fill="white"/>',
        '<style>text{font:15px Arial,sans-serif;fill:#263c47}.heading{font-size:19px;font-weight:bold}</style>',
        '<text x="16" y="30" class="heading">Individual rune rows matched</text>',
        '<text x="16" y="55">43 of 65 reference rows · fixed detector</text>',
        '<rect x="16" y="72" width="13" height="13" fill="#315e72"/><text x="36" y="84">Matched</text>',
        '<rect x="140" y="72" width="13" height="13" fill="#dce2e5"/><text x="160" y="84">Unmatched</text>']
    for i,page in enumerate(report['pages']):
        y = 120 + i*48
        n = len(page['runic_rows']); m = page['maximum_matched_rows']
        parts.append(f'<text x="16" y="{y+15}">{page["page"].upper()}</text>')
        if n:
            parts += [f'<rect x="100" y="{y}" width="{n*16}" height="21" fill="#dce2e5"/>',
                f'<rect x="100" y="{y}" width="{m*16}" height="21" fill="#315e72"/>',
                f'<text x="304" y="{y+16}">{m}/{n}</text>']
        else:
            parts.append(f'<text x="100" y="{y+16}">No reference rune rows</text>')
    parts += ['<text x="16" y="523">Eight selected layouts, not a random sample.</text>',
        '<text x="16" y="548">Matching requires interval overlap ≥ 0.5.</text>',
        '<text x="16" y="571">This does not test rune identity.</text></svg>']
    return '\n'.join(parts)+'\n'

if __name__ == '__main__':
    (HERE/'summary.svg').write_text(render(),encoding='utf-8',newline='\n')
