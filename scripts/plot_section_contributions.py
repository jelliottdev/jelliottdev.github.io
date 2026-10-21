"""Render the checked descriptive LP1 section contributions on one scale."""
import json
import math
from fractions import Fraction
from pathlib import Path
from audit_section_contributions import calculate

ROOT = Path(__file__).resolve().parents[1]


def render():
    report = json.loads((ROOT / 'exports/section-contributions.json').read_bytes())
    assert report == calculate()
    labels = ['Warning', 'Welcome', 'First koan', 'Second koan', 'Combined']
    vectors = [[float(Fraction(x)) for x in s['excess_runes']] for s in report['sections']]
    vectors.append([float(Fraction(x)) for x in report['combined_excess_runes']])
    limit = math.ceil(max(abs(x) for v in vectors for x in v) / 5) * 5
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 850" role="img" aria-labelledby="title desc">',
             '<title id="title">How sections contribute to column balance</title>',
             '<desc id="desc">Five panels on the same scale show excess rune length in each of sixteen columns. The combined panel adds the four sections. Positive and negative contributions can cancel.</desc>',
             '<rect width="380" height="850" fill="white"/>',
             '<style>text{font:14px Arial,sans-serif;fill:#25343a}.small{font-size:12px}</style>',
             '<text x="16" y="25">How sections contribute to column balance</text>',
             '<text x="16" y="47" class="small">Excess runes over word count × global mean</text>',
             '<text x="16" y="66" class="small">Same scale throughout · original 16-column order</text>']
    for i, (label, values) in enumerate(zip(labels, vectors)):
        y = 95 + 143*i
        zero = y + 59
        parts.append(f'<text x="16" y="{y}">{label}</text>')
        for tick in [-limit, 0, limit]:
            ty = zero - tick / limit * 40
            parts.extend([f'<line x1="42" x2="366" y1="{ty}" y2="{ty}" stroke="#d5dce0"/>',
                          f'<text x="36" y="{ty+4}" text-anchor="end" class="small">{tick}</text>'])
        for j, value in enumerate(values):
            height = abs(value)/limit*40
            top = zero-height if value >= 0 else zero
            parts.extend([f'<rect x="{45+j*20}" y="{top:.3f}" width="15" height="{height:.3f}" fill="{"#42687b" if value >= 0 else "#927654"}"/>',
                          f'<text x="{52.5+j*20}" y="{zero+57}" text-anchor="middle" class="small">{j+1}</text>'])
    parts.extend(['<text x="16" y="824" class="small">Column numbers 1–16 · no chance model fitted</text>', '</svg>'])
    return '\n'.join(parts)+'\n'


if __name__ == '__main__':
    (ROOT / 'exports/figures/section-contributions.svg').write_text(render(), encoding='utf-8', newline='\n')
