"""Plot declared ten-count bin probabilities; retain numeric tail in caption."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def figure():
    r = json.loads((HERE / 'results.json').read_bytes())
    x = lambda n: 44 + 296*n/650
    y = lambda p: 260 - 180*p/.25
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="370" viewBox="0 0 360 370" role="img" aria-labelledby="title desc">',
             '<title id="title">Adjacent matches under uniform additive keys</title>',
             '<desc id="desc">Binomial model with 12,901 within-page edges and match probability 1/29. Observed count 86 is far below the expected count 444.86. Bars show probability per ten-count bin; positions 650 and above are omitted from the plot but retained in the data.</desc>',
             '<rect width="360" height="370" fill="#faf9f5"/>',
             '<g font-family="Arial,sans-serif" fill="#263b45">',
             '<text x="16" y="25" font-size="17">Uniform-key model</text>',
             '<text x="16" y="48" font-size="13">Probability per 10-count bin</text>']
    for p in (0, .1, .2):
        parts.append(f'<path d="M44 {y(p):.2f}H340" stroke="#d7dbda"/><text x="37" y="{y(p)+4:.2f}" font-size="12" text-anchor="end">{p:.0%}</text>')
    for row in r['plot_bins'][:65]:
        height = 260-y(float(row['probability']))
        parts.append(f'<rect x="{x(row["start"]):.3f}" y="{260-height:.3f}" width="4.15" height="{height:.6f}" fill="#315f73"/>')
    for tick in (0, 200, 400, 600):
        parts.append(f'<text x="{x(tick):.2f}" y="281" font-size="12" text-anchor="middle">{tick}</text>')
    for value, label, color in [(r['observed_doublets'], 'Observed 86', '#985927'), (r['edges']/29, 'Expected 445', '#263b45')]:
        parts.append(f'<path d="M{x(value):.2f} 89V260" stroke="{color}" stroke-dasharray="4 3"/><text x="{x(value):.2f}" y="77" font-size="12" text-anchor="middle" fill="{color}">{label}</text>')
    parts.extend(['<text x="192" y="305" font-size="13" text-anchor="middle">Number of adjacent matches</text>',
                  '<text x="16" y="333" font-size="12">12,901 edges; page boundaries retained.</text>',
                  '<text x="16" y="353" font-size="12">Range shown: 0–649. Full bins in JSON.</text>', '</g></svg>'])
    return '\n'.join(parts)+'\n'


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true')
    args = p.parse_args()
    value = figure()
    path = HERE / 'distribution.svg'
    if args.check:
        assert path.read_text(encoding='utf-8') == value
        print('PASS: distribution figure matches saved bin probabilities')
    else:
        path.write_text(value, encoding='utf-8', newline='\n')
