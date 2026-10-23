"""Small-screen comparison of the seven pinned source model means."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = [
    ('M0_nofilter', 'No filter'),
    ('M1_ct_keyskip', 'Key skip'),
    ('M2_ct_rewrite', 'Output rewrite'),
    ('M2n_ct_nudge', 'Fixed nudge'),
    ('M3_ks_filtered', 'Key filter'),
    ('M4_pt_filtered', 'Text filter'),
    ('M5_ct_hard', 'Hard ban'),
]


def make():
    data = json.loads((HERE / 'source-results.json').read_text(encoding='utf-8'))
    obs = data['real']['lag1_rate'] * 100
    x0, span = 151, 145
    x = lambda pct: x0 + span * pct / 4
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 407" role="img" '
           'aria-labelledby="title desc">',
           '<title id="title">Seven filter models and the manuscript repeat rate</title>',
           '<desc id="desc">Observed adjacent repeats are 0.664 percent. Key skip, output rewrite and fixed nudge match that rate; no filter, key filter and text filter are near 3.5 percent; a hard ban produces zero.</desc>',
           '<rect width="320" height="407" fill="#f7f8fa"/>',
           '<text x="16" y="28" font-family="Arial,sans-serif" font-size="17" font-weight="700" fill="#202c34">Where is the repeat blocked?</text>',
           '<text x="16" y="51" font-family="Arial,sans-serif" font-size="13" fill="#4e5e69">Equal adjacent runes · percent of pairs</text>',
           f'<rect x="{x0}" y="67" width="{span}" height="291" fill="#edf1f4"/>']
    for pct in (0, 1, 2, 3, 4):
        xx = x(pct)
        out.append(f'<line x1="{xx:.1f}" y1="67" x2="{xx:.1f}" y2="358" stroke="#d1d9de"/>')
        out.append(f'<text x="{xx:.1f}" y="380" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#52636e">{pct}%</text>')
    xo = x(obs)
    out.append(f'<line x1="{xo:.1f}" y1="67" x2="{xo:.1f}" y2="358" stroke="#117491" stroke-width="2" stroke-dasharray="4 3"/>')
    for i, (key, label) in enumerate(LABELS):
        yy = 91 + i * 40
        rate = data['achieved_lag1'][key] * 100
        xx = x(rate)
        color = '#245770' if key in {'M1_ct_keyskip', 'M2_ct_rewrite'} else '#64727c'
        if key == 'M2n_ct_nudge':
            color = '#a35546'
        out.append(f'<text x="16" y="{yy+4}" font-family="Arial,sans-serif" font-size="13" fill="#26333c">{label}</text>')
        out.append(f'<circle cx="{xx:.1f}" cy="{yy}" r="5" fill="{color}"/>')
        if i < 6:
            out.append(f'<line x1="16" y1="{yy+19}" x2="304" y2="{yy+19}" stroke="#e0e5e8"/>')
    out.append('<text x="16" y="399" font-family="Arial,sans-serif" font-size="13" fill="#117491">Dashed line: observed 0.664%</text>')
    out.append('</svg>')
    return '\n'.join(out) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    target = HERE / 'filter-loci.svg'
    content = make()
    if args.check:
        assert target.read_text(encoding='utf-8') == content
        print('PASS: SVG matches pinned seven-model results')
    else:
        target.write_text(content, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
