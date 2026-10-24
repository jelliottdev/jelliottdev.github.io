import argparse,json,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent
def render():
    r=json.loads((HERE/'results.json').read_text(encoding='utf-8'));vals=sorted(x['ioc'] for x in r['null_maxima']);obs=r['observed']['ioc']
    lower=min(vals[0],obs)-.0005;upper=max(vals[-1],obs)+.0005
    def x(v):return 40+520*(v-lower)/(upper-lower)
    ticks=''.join(f'<line x1="{x(lower+(upper-lower)*i/4):.2f}" y1="285" x2="{x(lower+(upper-lower)*i/4):.2f}" y2="294" stroke="#23394c"/><text x="{x(lower+(upper-lower)*i/4):.2f}" y="325" text-anchor="middle" font-size="20">{lower+(upper-lower)*i/4:.4f}</text>' for i in range(5))
    dots=''.join(f'<circle cx="{x(v):.2f}" cy="{195+(i%4)*10}" r="3" fill="#72859a"/>' for i,v in enumerate(vals))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="430" viewBox="0 0 600 430" role="img" aria-labelledby="title desc">
<title id="title">Shifted page-pair concentration and global shuffle maxima</title><desc id="desc">The actual maximum IoC is {obs:.6f}. {r['null_exceedances']} of128 shuffled global maxima meet or exceed it.</desc>
<rect width="600" height="430" fill="white"/><g font-family="Arial,sans-serif" fill="#193044"><text x="24" y="34" font-size="24">Does shifting reveal an unusual pattern?</text>
<text x="24" y="73" font-size="21">331,908 page-pair alignments</text>
<text x="24" y="120" font-size="21">Actual pages</text><text x="350" y="120" font-size="21">Score {obs:.5f}</text><line x1="{x(obs):.2f}" y1="140" x2="{x(obs):.2f}" y2="280" stroke="#a14f32" stroke-width="3"/>
<text x="24" y="168" font-size="21">128 shuffled searches</text>{dots}<line x1="40" y1="285" x2="560" y2="285" stroke="#23394c"/>{ticks}
<text x="24" y="365" font-size="20">Higher scores mean more repeated differences.</text>
<text x="24" y="411" font-size="21">{r['null_exceedances']}/128 shuffled searches are at least as strong.</text></g></svg>'''
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();target=HERE/'global-shift-max.svg';svg=render()
    if a.check:assert target.read_text(encoding='utf-8')==svg;print('PASS: plot current')
    else:target.write_text(svg,encoding='utf-8',newline='\n')
