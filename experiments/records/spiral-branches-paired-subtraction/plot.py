"""Plot selected IoC score beside both complete control distributions."""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
TARGET = BASE / "score-controls.svg"


def chart():
    data = json.loads((BASE / "results.json").read_text(encoding="utf-8"))
    groups = [("Circular shifts · 2,882", sorted(data["controls"]["nonzero_circular_shifts"]["maxima"])),
              ("Within-page shuffles · 999", sorted(data["controls"]["within_page_shuffle"]["maxima"]))]
    observed = data["observed_max_pair_count"]
    low, high = 285000, 291000
    x = lambda value: round(52 + (value - low) * 340 / (high - low), 2)
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 245" role="img" aria-labelledby="title desc">',
             '<title id="title">Selected pair-count score against two controls</title>',
             '<desc id="desc">The observed best of five variants is 287,504 ordered equal-rune pairs. It falls within both circular-shift and within-page-shuffle distributions.</desc>',
             '<rect width="420" height="245" fill="#fff"/>',
             '<text x="52" y="18" font-family="system-ui,sans-serif" font-size="12" fill="#1d303b">Best of five variants: 287,504</text>']
    for y, (label, values) in zip((78, 158), groups):
        q1, median, q3 = (values[round((len(values)-1)*p)] for p in (0.25, 0.5, 0.75))
        lines.extend([f'<text x="52" y="{y-27}" font-family="system-ui,sans-serif" font-size="11" fill="#35454d">{label}</text>',
                      f'<path d="M {x(values[0])} {y} H {x(values[-1])}" stroke="#6c8490" stroke-width="2"/>',
                      f'<path d="M {x(values[0])} {y-6} V {y+6} M {x(values[-1])} {y-6} V {y+6}" stroke="#6c8490" stroke-width="2"/>',
                      f'<rect x="{x(q1)}" y="{y-11}" width="{round(x(q3)-x(q1),2)}" height="22" fill="#c8d8df" stroke="#456777"/>',
                      f'<path d="M {x(median)} {y-11} V {y+11}" stroke="#244858" stroke-width="2"/>'])
    lines.extend([f'<path d="M {x(observed)} 28 V 184" stroke="#9a573b" stroke-width="2" stroke-dasharray="4 3"/>',
                  '<text x="52" y="205" font-family="system-ui,sans-serif" font-size="10" fill="#35454d">285,000</text>',
                  '<text x="222" y="205" text-anchor="middle" font-family="system-ui,sans-serif" font-size="10" fill="#35454d">288,000</text>',
                  '<text x="392" y="205" text-anchor="end" font-family="system-ui,sans-serif" font-size="10" fill="#35454d">291,000</text>',
                  '<text x="222" y="231" text-anchor="middle" font-family="system-ui,sans-serif" font-size="11" fill="#35454d">Ordered equal-rune pairs</text>',
                  '</svg>'])
    return ('\n'.join(lines) + '\n').encode('utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = chart()
    if args.check:
        assert TARGET.read_bytes() == output
        print('PASS: saved control chart')
    else:
        TARGET.write_bytes(output)
        print(TARGET)
