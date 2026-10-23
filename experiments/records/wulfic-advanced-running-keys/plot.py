"""Compact control-power and whole-search score figure."""
import argparse,json
from pathlib import Path
H=Path(__file__).resolve().parent
def make():
    c=json.loads((H/'control-results.json').read_text(encoding='utf8'))['control']
    r=json.loads((H/'results.json').read_text(encoding='utf8'))
    on=sum(z['full_recovery'] for z in c['one_page'] if z['kind']=='on_grid')
    off=sum(z['full_recovery'] for z in c['one_page'] if z['kind']=='off_grid')
    n=sorted(z['ranking_score'] for z in r['null_maxima']);mid=n[len(n)//2];mx=n[-1];observed=r['summary']['top_ranking_score']
    rows=[('LP2 best',observed,'#2d6780',208),('Shuffle middle',mid,'#879ba6',249),('Shuffle highest',mx,'#5b6d76',290)]
    bars=''
    for name,val,color,y in rows:
        bars+=f'<text x="12" y="{y}" font-size="14">{name}</text><rect x="140" y="{y-15}" width="{val*0.83:.1f}" height="19" fill="{color}"/><text x="302" y="{y}" text-anchor="end" font-size="14">{val:.0f}</text>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="355" viewBox="0 0 320 355" font-family="Arial, sans-serif" role="img" aria-labelledby="title desc"><title id="title">A known message is found at sampled offsets but missed between them</title><desc id="desc">Four of four on-grid full-reading plants recovered, zero of four off-grid plants recovered. The manuscript best source rank score is {observed:.1f}; the middle and highest of 49 full-search shuffles are {mid:.1f} and {mx:.1f}; 41 shuffles reach at least the manuscript score.</desc><rect width="320" height="355" fill="#fff"/><text x="12" y="25" font-size="17" font-weight="bold" fill="#152e3b">Running-key source search</text><text x="12" y="52" font-size="14" fill="#3c515e">Full known reading recovered</text><text x="12" y="85" font-size="14">Sampled offset 300</text><rect x="171" y="66" width="108" height="25" fill="#2d6780"/><text x="309" y="85" text-anchor="end" font-size="14" fill="#25343d">{on} / 4</text><text x="12" y="125" font-size="14">Unsampled offset 137</text><rect x="171" y="106" width="108" height="25" fill="#e5e9eb"/><text x="309" y="125" text-anchor="end" font-size="14">{off} / 4</text><line x1="12" y1="150" x2="308" y2="150" stroke="#c9d0d4"/><text x="12" y="176" font-size="14" fill="#3c515e">Best source rank score</text>{bars}<text x="12" y="320" font-size="14" fill="#243b46">41 of 49 shuffled searches scored as high.</text><text x="12" y="342" font-size="12" fill="#52636a">A source score is not a verified reading.</text></svg>\n'''
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();p=H/'comparison.svg';s=make()
    if a.check:assert p.read_text(encoding='utf8')==s;print('PASS SVG')
    else:p.write_text(s,encoding='utf8',newline='\n')
