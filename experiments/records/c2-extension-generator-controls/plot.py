"""Neutral responsive SVG: seven seeds and medians for each decoder/mechanism."""
import argparse
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
LABELS = ['Bash model · paired skip', 'Perl model · paired skip', 'TeX PGF · paired skip',
          'TeX LCG · paired skip', 'SHA-256 counter · paired skip', 'Python 2.7 model · paired skip',
          'Python 2.7 model · random drift', 'Python 2.7 model · ten fixed drifts']


def render():
    results = json.loads((HERE/'results.json').read_text())
    saved = json.loads((HERE/'source-control.json').read_text())
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 1080" role="img" aria-labelledby="title desc" style="max-width:100%;height:auto">',
             '<title id="title">Matching the decoder to the planted rule improves recovery</title>',
             '<desc id="desc">Eight generator and plant pairs, seven seeds each. Matching-rule median recovery is 98.3 to 100 percent; baseline medians are 10 to 32.9 percent. All keys are supplied. Vertical line marks the 90 percent source gate.</desc>',
             '<rect width="560" height="1080" fill="#fff"/>',
             '<g font-family="Arial,sans-serif" fill="#222" font-size="22">',
             '<text x="24" y="34" font-size="25">Recovery with the correct key</text>',
             '<text x="24" y="66">56 plants using seven plaintext windows</text>',
             '<text x="24" y="96">240 runes · small dots: seeds · large: medians</text>',
             '<circle cx="31" cy="122" r="5" fill="#344b61"/><text x="45" y="129">Matching rule</text>',
             '<circle cx="251" cy="122" r="5" fill="#999"/><text x="265" y="129">Single-skip baseline</text>']
    for v in range(0,101,25):
        x=60+v*4.4
        parts.append(f'<text x="{x}" y="162" text-anchor="middle" font-size="20">{v}%</text>')
    for i, (summary,label) in enumerate(zip(results['summaries'],LABELS)):
        y=192+i*104
        generator, mechanism = label.split(' · ')
        parts += [f'<text x="24" y="{y}" font-weight="bold">{generator}</text>',
                  f'<text x="24" y="{y+26}" font-size="20">{mechanism}</text>']
        chart_y=y+59
        for v in range(0,101,25):
            x=60+v*4.4
            parts.append(f'<line x1="{x}" y1="{chart_y-19}" x2="{x}" y2="{chart_y+19}" stroke="#e5e5e5"/>')
        parts.append(f'<line x1="456" y1="{chart_y-19}" x2="456" y2="{chart_y+19}" stroke="#666" stroke-dasharray="3 3"/>')
        for kind,offset,color in [('beam',9,'#999'),('dec',-9,'#344b61')]:
            values=[r[kind+'_rec'] for r in saved['axes'][summary['axis']]['rows']]
            med=summary['modeled_median' if kind=='dec' else 'baseline_median']
            for value in values:
                parts.append(f'<circle cx="{60+value*440:.3f}" cy="{chart_y+offset}" r="3" fill="{color}" opacity="0.45"/>')
            parts.append(f'<circle cx="{60+med*440:.3f}" cy="{chart_y+offset}" r="6" fill="{color}" stroke="white" stroke-width="1"/>')
    parts += ['<text x="24" y="1031" font-size="20">Dashed mark: source gate at 90% recovery</text>',
              '<text x="24" y="1063" font-size="20">Tool controls; no manuscript key search.</text></g></svg>']
    return '\n'.join(parts)+'\n'


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); args=parser.parse_args()
    path=HERE/'recovery.svg'; data=render()
    if args.check: assert path.read_text(encoding='utf-8')==data; print('PASS: SVG matches results')
    else: path.write_text(data,encoding='utf-8')
