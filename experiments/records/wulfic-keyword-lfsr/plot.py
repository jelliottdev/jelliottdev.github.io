"""A readable source-gate chart at 320 px."""
import argparse
import json
from pathlib import Path
H=Path(__file__).resolve().parent
def make():
    r=json.loads((H/'results.json').read_text(encoding='utf8'))
    pages=[]
    for row in r['observed']:
        if row['page'] not in pages:pages.append(row['page'])
    best=[max(x['ioc'] for x in r['observed'] if x['page']==p) for p in pages]
    x0=84;scale=166/1.2
    bars=''
    for i,(page,val) in enumerate(zip(pages,best)):
        y=72+i*26;w=round(val*scale,1)
        bars+=f'<text x="12" y="{y+15}" font-size="14">{page.upper()}</text><rect x="{x0}" y="{y}" width="{w}" height="18" fill="#2c6881"/><text x="266" y="{y+15}" font-size="13">{val:.2f}</text>'
    gate=x0+1.2*scale
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="398" viewBox="0 0 320 398" font-family="Arial, sans-serif" role="img" aria-labelledby="title desc"><title id="title">No page cleared the source's LFSR reporting gate</title><desc id="desc">Best normalized index of coincidence over 40 LFSR settings on each of ten pages. Values range from 1.02 to 1.10; the source reports only values above 1.2. A 209-rune known-reading plant measured 2.06 and recovered exactly.</desc><rect width="320" height="398" fill="#fff"/><text x="12" y="24" font-size="17" font-weight="bold" fill="#142e3a">Keyword-seeded LFSR</text><text x="12" y="48" font-size="14" fill="#41515b">Best score on each page · gate above 1.20</text><line x1="{gate:.1f}" y1="68" x2="{gate:.1f}" y2="331" stroke="#a64242" stroke-width="2" stroke-dasharray="4 3"/>{bars}<text x="12" y="353" font-size="14" fill="#203944">0 of 400 settings cleared the gate.</text><text x="12" y="377" font-size="13" fill="#465964">Known-reading control: 2.06; exact recovery.</text></svg>\n'''
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();value=make();p=H/'comparison.svg'
    if a.check:assert p.read_text(encoding='utf8')==value;print('PASS SVG')
    else:p.write_text(value,encoding='utf8',newline='\n')
