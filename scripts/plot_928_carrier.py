"""Draw the checked carrier inventory on a shared word-position scale."""
import json
from pathlib import Path
from audit_928_carrier import calculate

ROOT = Path(__file__).resolve().parents[1]


def render():
    report = json.loads((ROOT / 'exports/carrier-928.json').read_bytes())
    assert report == calculate(), 'Inventory differs from current source'
    total = report['total_words']
    assert total == 928
    x = lambda n: 20 + 340 * n / total
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 440" role="img" aria-labelledby="title desc">',
             '<title id="title">Where the 928-word carrier divides</title>',
             '<desc id="desc">Mayfly occupies words 1–224, Wing and Tree 225–550, and Cuneiform 551–928. The halfway split after word 464 lies within Wing and Tree, on LP2-30.</desc>',
             '<rect width="380" height="440" fill="white"/>',
             '<style>text{font:16px Arial,sans-serif;fill:#25343a}.small{font-size:13px}</style>',
             '<text x="20" y="28">Where the carrier divides</text>',
             '<text x="20" y="51" class="small">928 rune-words · headings included</text>']
    offset = 0
    for i, (group, label) in enumerate(zip(report['groups'], ['Mayfly', 'Wing and Tree', 'Cuneiform'])):
        y = 84 + 83 * i
        end = offset + group['words']
        parts.extend([f'<text x="20" y="{y}">{label}</text>',
                      f'<text x="360" y="{y}" text-anchor="end" class="small">words {offset + 1}–{end}</text>',
                      f'<rect x="20" y="{y + 12}" width="340" height="24" fill="#eef1f2"/>',
                      f'<rect x="{x(offset):.3f}" y="{y + 12}" width="{x(end)-x(offset):.3f}" height="24" fill="#42687b"/>',
                      f'<text x="20" y="{y + 55}" class="small">{group["pages"][0].upper()}–{group["pages"][-1][-2:]} · {group["words"]} words</text>'])
        offset = end
    assert offset == total
    parts.extend(['<path d="M190 94 V294" stroke="#9a5526" stroke-width="2" stroke-dasharray="5 4"/>',
                  '<text x="20" y="325">Halfway: after word 464</text>',
                  '<text x="20" y="350" class="small">LP2-30 · final printed row</text>',
                  '<text x="20" y="374" class="small">An ordinary word separator, not a group boundary.</text>',
                  '<text x="20" y="413" class="small">Shared scale: all 928 positions on every row.</text>',
                  '</svg>'])
    return '\n'.join(parts) + '\n'


if __name__ == '__main__':
    (ROOT / 'exports/figures/carrier-928.svg').write_text(render(), encoding='utf-8', newline='\n')
