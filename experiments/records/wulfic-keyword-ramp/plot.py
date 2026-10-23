"""Small-screen source-score comparison from frozen result values."""
import argparse
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def make():
    r=json.loads((HERE/'results.json').read_text(encoding='utf8'))
    n=r['null_maxima'];top=r['summary']['observed_max'];median=sorted(n)[len(n)//2];mx=max(n)
    # A single source-score scale for the observed and shuffled full-grid maxima.
    x0=126;scale=1.6
    lines=[(60,'LP2 best',top,'#225b77'),(122,'Shuffle middle',median,'#9daab0'),(184,'Shuffle highest',mx,'#6d7b82')]
    bars=''
    for y,label,val,color in lines:
        tx=min(300,int(x0+val*scale+5));anchor='end' if x0+val*scale+5>300 else 'start'
        bars+=f'<text x="12" y="{y-8}" font-size="14">{label}</text><rect x="{x0}" y="{y-24}" width="{int(val*scale)}" height="20" fill="{color}"/><text x="{tx}" y="{y-8}" font-size="14" text-anchor="{anchor}">{val}</text>'
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="304" viewBox="0 0 320 304" role="img" aria-labelledby="title desc" font-family="Arial, sans-serif"><title id="title">Keyword plus position step: source score comparison</title><desc id="desc">The best LP2 source word score is {top}. The middle of 199 complete shuffled searches is {median}, and the highest is {mx}; 10 shuffles meet or exceed the LP2 value. A planted known reading scores 380, outside this plotting scale.</desc><rect width="320" height="304" fill="#fff"/><text x="12" y="25" font-size="17" font-weight="bold" fill="#162c38">Keyword + position step</text><line x1="12" y1="34" x2="308" y2="34" stroke="#cbd3d7"/>{bars}<text x="12" y="221" font-size="14" fill="#26343b">10 of 199 full searches scored ≥ {top}.</text><text x="12" y="247" font-size="14" fill="#26343b">Known-reading plant: 380 and exact recovery.</text><text x="12" y="275" font-size="13" fill="#4c5a60">Source word-count score; higher is not proof.</text></svg>'''
    return svg+'\n'
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();p=HERE/'comparison.svg';value=make()
    if a.check:assert p.read_text(encoding='utf8')==value;print('PASS SVG')
    else:p.write_text(value,encoding='utf8',newline='\n')
