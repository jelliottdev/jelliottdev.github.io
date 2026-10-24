"""Render saved whole-family maxima and known-input identification limits."""
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def render():
    r=json.loads((HERE/'results.json').read_bytes())
    best=r['observed']['best']['score'];bar=r['hit_bar']
    def x(value):return 40+(value+6.4)/1.4*280
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 950" width="360" height="950" role="img" aria-labelledby="title desc">',
         '<title id="title">Every starting pair across the fixed two-rune feedback family</title>',
         '<desc id="desc">The manuscript search maximum is below both frozen score gates. Shuffled dots are maxima over the entire family. Known-input controls show that high score does not guarantee the complete true output.</desc>',
         '<rect width="360" height="950" fill="white"/>',
         '<g fill="#252525" font-family="Arial,sans-serif" font-size="20">',
         '<text x="20" y="32" font-size="23">Did any starting pair pass?</text>',
         '<text x="20" y="69">Fixed two-rune feedback rules.</text>',
         '<text x="20" y="101">A dot is a whole-search best.</text>',
         '<text x="20" y="150">Manuscript search</text>',
         f'<text x="20" y="179">Best score: {best:.3f}</text>',
         '<line x1="40" y1="211" x2="320" y2="211" stroke="#ddd"/>',
         f'<circle cx="{x(best):.2f}" cy="211" r="7" fill="#222"/>',
         '<text x="20" y="265">49 shuffled full searches</text>']
    for i,row in enumerate(r['null_global_witnesses']):
        out.append(f'<circle cx="{x(row["best"]["score"]):.2f}" cy="{299+(i%5)*10}" r="3" fill="#999"/>')
    out += [f'<line x1="{x(-5.5):.2f}" y1="192" x2="{x(-5.5):.2f}" y2="370" stroke="#aaa" stroke-dasharray="3 5"/>',
            f'<line x1="{x(bar):.2f}" y1="192" x2="{x(bar):.2f}" y2="370" stroke="#555" stroke-dasharray="6 5"/>']
    for value in (-6.3,-5.8,-5.3):out.append(f'<text x="{x(value):.2f}" y="402" text-anchor="middle">{value:.1f}</text>')
    out += ['<text x="20" y="443">Higher scores are stronger.</text>',
            '<text x="20" y="477">Absolute gate: −5.5.</text>',
            f'<text x="20" y="510">Combined pass gate: {bar:.3f}.</text>',
            '<text x="20" y="543">Requires the shuffled maximum</text>',
            '<text x="20" y="570">plus 0.5, and at least −5.5.</text>',
            f'<text x="20" y="614">{r["null_ge_observed"]}/49 shuffled searches</text>',
            '<text x="20" y="641">scored at least as highly.</text>',
            '<line x1="20" y1="673" x2="340" y2="673" stroke="#ddd"/>',
            '<text x="20" y="712" font-size="22">Known-input limitation</text>',
            '<text x="20" y="750">Given true keys: 336/336 recover.</text>',
            '<text x="20" y="783">Search selects whole truth:</text>',
            '<text x="20" y="816">264/336 constructed cases.</text>',
            '<text x="20" y="855">These reuse only two passages.</text>',
            '<text x="20" y="914">No cipher-family rejection.</text>',
            '</g></svg>']
    return ('\n'.join(out)+'\n').encode('utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    data=render();path=HERE/'family-score-screen.svg'
    if args.check:
        assert path.read_bytes()==data,'Chart differs from saved measurements.'
        print('PASS: saved family chart matches whole-search/control measurements.')
    else:path.write_bytes(data)
