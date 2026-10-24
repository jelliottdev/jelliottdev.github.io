import argparse,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def render():
    r=json.loads((HERE/'results.json').read_text(encoding='utf-8'));vals=sorted(x['score'] for x in r['null_maxima']);obs=r['observed']['score'];lo=min(vals[0],obs)-.005;hi=max(vals[-1],obs)+.005
    def x(v):return 40+520*(v-lo)/(hi-lo)
    ticks=''.join(f'<line x1="{x(lo+(hi-lo)*i/4):.2f}" y1="270" x2="{x(lo+(hi-lo)*i/4):.2f}" y2="279" stroke="#23394c"/><text x="{x(lo+(hi-lo)*i/4):.2f}" y="310" text-anchor="middle" font-size="20">{lo+(hi-lo)*i/4:.2f}</text>' for i in range(5))
    dots=''.join(f'<circle cx="{x(v):.2f}" cy="{183+(i%4)*10}" r="3" fill="#718399"/>' for i,v in enumerate(vals));plant=r['positive_controls'][0]['best']['score']
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="460" viewBox="0 0 600 460" role="img" aria-labelledby="title desc">
<title id="title">Do shifted page pairs reveal English?</title><desc id="desc">Across 995,724 direct readings, the strongest actual English score is {obs:.5f}. {r['null_at_or_above_observed']} of 128 shuffled searches score at least as highly. Known Warning controls score {plant:.3f}.</desc><rect width="600" height="460" fill="white"/>
<g font-family="Arial,sans-serif" fill="#193044"><text x="24" y="35" font-size="24">Do shifted page pairs reveal English?</text><text x="24" y="73" font-size="21">995,724 direct arithmetic readings</text>
<text x="24" y="116" font-size="21">Actual pages: {obs:.4f}</text><line x1="{x(obs):.2f}" y1="131" x2="{x(obs):.2f}" y2="265" stroke="#a14f32" stroke-width="3"/>
<text x="24" y="161" font-size="21">128 shuffled searches</text>{dots}<line x1="40" y1="270" x2="560" y2="270" stroke="#23394c"/>{ticks}
<text x="24" y="350" font-size="20">Higher scores mean more English-like output.</text><text x="24" y="391" font-size="21">{r['null_at_or_above_observed']}/128 shuffled searches score at least as highly.</text>
<text x="24" y="437" font-size="20">Known Warning plants: {plant:.3f}; gate: −5.5</text></g></svg>'''
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();target=HERE/'english-shift-max.svg';svg=render()
    if a.check:assert target.read_text(encoding='utf-8')==svg;print('PASS: plot current')
    else:target.write_text(svg,encoding='utf-8',newline='\n')
