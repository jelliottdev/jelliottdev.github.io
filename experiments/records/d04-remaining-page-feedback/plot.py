import argparse,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def render():
    r=json.loads((HERE/'results.json').read_text(encoding='utf-8'));p=min(c['true_score'] for c in r['gate']['controls']);actual=r['observed']['score'];lo=min(-7.3,actual-.1);hi=-4.2
    def x(v):return 40+520*(v-lo)/(hi-lo)
    ticks=''.join(f'<text x="{x(v):.2f}" y="286" text-anchor="middle" font-size="20">{v:.1f}</text>' for v in [-7,-6,-5])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="420" viewBox="0 0 600 420" role="img" aria-labelledby="t d"><title id="t">Does feedback from earlier runes reveal English?</title><desc id="d">52 additional pages and 1054976 settings. Best actual score {actual:.4f}; known Warning controls score {p:.4f}. The source signal line is minus5.2.</desc><rect width="600" height="420" fill="white"/><g font-family="Arial,sans-serif" fill="#25323c"><text x="24" y="35" font-size="23">Do earlier ciphertext runes supply the key?</text><text x="24" y="74" font-size="21">52 more pages; 1,054,976 settings</text>
<text x="24" y="116" font-size="21">Strongest actual page</text><circle cx="{x(actual):.2f}" cy="140" r="7" fill="#536675"/><text x="470" y="116" font-size="21">{actual:.4f}</text>
<text x="24" y="182" font-size="21">Known Warning controls</text><circle cx="{x(p):.2f}" cy="207" r="7" fill="#536675"/><text x="470" y="182" font-size="21">{p:.4f}</text>
<line x1="{x(-5.2):.2f}" y1="96" x2="{x(-5.2):.2f}" y2="258" stroke="#777" stroke-dasharray="5 5"/><line x1="40" y1="260" x2="560" y2="260" stroke="#25323c"/>{ticks}<text x="24" y="325" font-size="20">Higher scores mean more English-like output.</text><text x="24" y="367" font-size="21">Source signal line: −5.2</text><text x="24" y="402" font-size="21">{r['above_gate']} tested settings reach that line.</text></g></svg>'''
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();dest=HERE/'feedback-pages.svg';svg=render()
    if a.check:assert dest.read_text(encoding='utf-8')==svg;print('PASS: plot current')
    else:dest.write_text(svg,encoding='utf-8',newline='\n')
