"""Render all languages and representations with shared styling and axes."""
import argparse
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def figure():
    r=json.loads((HERE/'results.json').read_bytes())
    names=json.loads((ROOT/'experiments/plans/target-sized-language-controls.json').read_bytes())['languages']
    def value(x):return x['numerator']/x['denominator']
    def x(v):return 110+v/0.45*226
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="1200" viewBox="0 0 360 1200" role="img" aria-labelledby="title desc">',
         '<title id="title">Equal-size language samples and manuscript distances</title>',
         '<desc id="desc">All eight languages use the same styling. Blue ranges show the minimum and maximum reference-sample distances to their own language profile. Dark diamonds show the manuscript distance. Each sample has 2896 tokens. Three panels use the same zero to 0.45 scale.</desc>',
         '<rect width="360" height="1200" fill="#faf9f5"/><g font-family="Arial,sans-serif" fill="#263b45">',
         '<text x="14" y="25" font-size="17" font-weight="bold">Nearest is not necessarily close</text>',
         '<text x="14" y="48" font-size="13">2,896 tokens per reference sample</text>',
         '<path d="M16 70H46" stroke="#315f73" stroke-width="6"/><text x="56" y="74" font-size="12">Observed reference-sample range</text>',
         '<path d="M31 85l5 5-5 5-5-5Z" fill="#263b45"/><text x="56" y="94" font-size="12">Manuscript distance to that profile</text>']
    for panel,(mode,label) in enumerate([('letters','Letters'),('folded','Accent-folded letters'),('gp-length','GP grouping sensitivity')]):
        top=126+panel*340
        svg.append(f'<text x="14" y="{top}" font-size="16" font-weight="bold">{label}</text>')
        for tick in (0,0.1,0.2,0.3,0.4):
            xx=x(tick)
            svg.append(f'<path d="M{xx:.2f} {top+14}V{top+270}" stroke="#d9dfdf"/><text x="{xx:.2f}" y="{top+290}" text-anchor="middle" font-size="11">{tick:g}</text>')
        for row,code in enumerate(sorted(names,key=names.get)):
            y=top+29+row*33
            limits=r['modes'][mode]['languages'][code]['true_language_distance_range']
            lo,hi=x(value(limits['minimum'])),x(value(limits['maximum']))
            point=x(value(r['modes'][mode]['target_distances'][code]))
            svg.append(f'<text x="14" y="{y+4}" font-size="13">{names[code]}</text><path d="M{lo:.3f} {y}H{hi:.3f}" stroke="#315f73" stroke-width="6"/><path d="M{point:.3f} {y-5}l5 5-5 5-5-5Z" fill="#263b45"/>')
        svg.append(f'<text x="110" y="{top+311}" font-size="11">Total variation distance; lower is closer</text>')
    svg.extend(['<text x="14" y="1165" font-size="12">Ranges are descriptive, not confidence limits.</text>',
                '<text x="14" y="1185" font-size="12">Equal-size blocks need not cover identical passages.</text>','</g></svg>'])
    return '\n'.join(svg)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    content=figure();target=HERE/'comparison.svg'
    if a.check:assert target.read_text(encoding='utf-8')==content
    else:target.write_text(content,encoding='utf-8',newline='\n')
    print('All-language figure verified' if a.check else 'All-language figure written')
