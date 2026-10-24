"""Readable static fallback from compact measured results; no model execution."""
import argparse,json
from pathlib import Path
H=Path(__file__).resolve().parent
def build():
    r=json.loads((H/'results.json').read_bytes());p=r['predictors'];counts=[sum(x['uniform_classification']==k for x in p) for k in ('better','equivalent','worse')];best=max(p,key=lambda x:x['gain_over_uniform'])
    s=['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="790" viewBox="0 0 360 790">','<rect width="360" height="790" fill="white"/>','<g font-family="Arial,sans-serif" font-size="20" fill="#222">','<text x="20" y="34">Next-rune predictions</text>','<text x="20" y="68">None crossed the fixed gate.</text>','<line x1="20" x2="340" y1="91" y2="91" stroke="#ccc"/>','<text x="20" y="126">16 models vs a uniform guess</text>']
    x=20
    for count,color in zip(counts,('#444','#eee','#aaa')):
        for _ in range(count):s.append(f'<rect x="{x}" y="148" width="16" height="28" fill="{color}" stroke="#777"/>');x+=20
    for y,label in [(211,f'{counts[0]} slightly better'),(244,f'{counts[1]} equivalent within tolerance'),(277,f'{counts[2]} worse')]:s.append(f'<text x="20" y="{y}">{label}</text>')
    s.extend([f'<text x="20" y="322">Largest gain: {best["gain_over_uniform"]:.6f}</text>','<text x="20" y="352">bits per rune below uniform.</text>',f'<text x="20" y="386">{best["nulls_at_least_as_good"]} controls did at least as well.</text>','<line x1="20" x2="340" y1="412" y2="412" stroke="#ccc"/>','<text x="20" y="450">Combined 26-measurement test</text>',f'<text x="20" y="489">{r["family"]["controls_at_least_as_strong"]} of 1,000 filtered controls</text>','<text x="20" y="520">scored at least as strongly.</text>','<text x="20" y="558">Fixed 1% gate: not passed.</text>','<line x1="20" x2="340" y1="583" y2="583" stroke="#ccc"/>','<text x="20" y="622">Packed LZMA flagged none of</text>','<text x="20" y="653">18 synthetic examples.</text>','<text x="20" y="694">Includes 12 strong patterns.</text>','<text x="20" y="725">This does not prove randomness</text>','<text x="20" y="756">or rule out a plaintext.</text>','</g></svg>']);return '\n'.join(s)+'\n'
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();f=H/'predictive-controls.svg';value=build()
    if a.check:assert f.read_text(encoding='utf8')==value;print('PASS saved result visual')
    else:f.write_text(value,encoding='utf8',newline='\n')
