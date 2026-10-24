"""Draw the fixed-grid result and exact three-position primer-error identity."""
from pathlib import Path
import argparse
import json

HERE=Path(__file__).resolve().parent


def svg():
    r=json.loads((HERE/'results.json').read_bytes())
    best=r['observed']['best']['score'];diagonal=r['observed']['diagonal_best']
    def x(v):return 40+(v+6.7)/1.3*280
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 1060" width="360" height="1060" role="img" aria-labelledby="title desc">',
         '<title id="title">Unequal two-rune starts did not pass the fixed English-score gate</title>',
         '<desc id="desc">All841 starts on55pages were searched. The best score was minus6.504, below the minus5.5 gate. Forty of49 shuffled complete searches scored at least as highly. For this fixed rule, a primer error repeats every three positions.</desc>',
         '<rect width="360" height="1060" fill="white"/>',
         '<g fill="#242424" font-family="Arial,sans-serif" font-size="20">',
         '<text x="20" y="32" font-size="23">Did unequal starts help?</text>',
         '<text x="20" y="69">46,255 page/key-pair cases.</text>',
         '<text x="20" y="101">Higher scores are stronger.</text>',
         f'<line x1="{x(-5.5):.2f}" y1="133" x2="{x(-5.5):.2f}" y2="442" stroke="#777" stroke-dasharray="5 5"/>',
         '<text x="20" y="157">Equal pairs (a,a): 29</text>',
         f'<text x="20" y="184">Best: {diagonal:.3f}</text>',
         '<line x1="40" y1="211" x2="320" y2="211" stroke="#ddd"/>',
         f'<circle cx="{x(diagonal):.2f}" cy="211" r="6" fill="#888"/>',
         '<text x="20" y="257">All pairs (a,b): 29 × 29</text>',
         f'<text x="20" y="284">Best: {best:.3f}</text>',
         '<line x1="40" y1="311" x2="320" y2="311" stroke="#ddd"/>',
         f'<circle cx="{x(best):.2f}" cy="311" r="7" fill="#222"/>',
         '<text x="20" y="359">49 shuffled full searches</text>']
    for i,row in enumerate(r['nulls']):
        out.append(f'<circle cx="{x(row["best"]["score"]):.2f}" cy="{390+(i%5)*9}" r="3" fill="#aaa"/>')
    for value in (-6.5,-6.0,-5.5):
        out.append(f'<text x="{x(value):.2f}" y="475" text-anchor="middle">{value:.1f}</text>')
    out += ['<text x="20" y="515">Pass gate: −5.5.</text>',
            f'<text x="20" y="549">{r["null_ge_observed"]}/49 shuffled searches</text>',
            '<text x="20" y="576">scored at least as highly.</text>',
            '<line x1="20" y1="607" x2="340" y2="607" stroke="#ddd"/>',
            '<text x="20" y="645" font-size="22">Why the start still matters</text>',
            '<text x="20" y="683">Example output errors:</text>']
    for i,label in enumerate(('3','5','21','3','5','21')):
        xx=20+i*54
        out += [f'<rect x="{xx}" y="704" width="50" height="46" fill="#f1f1f1"/>',
                f'<text x="{xx+25}" y="733" text-anchor="middle" font-size="{20}">{label}</text>']
    out += ['<text x="20" y="790">21 = −(3 + 5) mod 29.</text>',
            '<text x="20" y="817">Next error = minus the</text>',
            '<text x="20" y="844">previous two errors.</text>',
            '<text x="20" y="885">The three errors repeat.</text>',
            '<text x="20" y="912">No automatic “lock on”.</text>',
            '<text x="20" y="960">Fixed two-plaintext-rune</text>',
            '<text x="20" y="987">sum rule only, mod 29.</text>',
            '<text x="20" y="1032">No general autokey exclusion.</text>',
            '</g></svg>']
    return ('\n'.join(out)+'\n').encode('utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    data=svg();p=HERE/'primer-grid.svg'
    if args.check:
        assert p.read_bytes()==data,'Chart differs from saved measurements.'
        print('PASS: chart matches saved measurements.')
    else:p.write_bytes(data)
