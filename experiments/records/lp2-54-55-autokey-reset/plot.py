"""Write a compact period profile and its CSV from saved experiment results."""
import csv
from fractions import Fraction
import json
import math
from pathlib import Path
import sys


def main(here):
    r=json.loads((here/'results.json').read_text(encoding='utf-8'))
    periods=sorted({x['period'] for x in r['observed']})
    profile=[]
    for p in periods:
        rows=[x for x in r['observed'] if x['period']==p]
        peak=max(Fraction(x['numerator'],x['denominator']) for x in rows)
        zero=next(x for x in rows if x['mask']==0)
        profile.append({'period':p,'no_interruptions':float(Fraction(zero['numerator'],zero['denominator'])),'best_of_64_masks':float(peak),'best_exact':str(peak),'winning_masks':' '.join(str(x['mask']) for x in rows if Fraction(x['numerator'],x['denominator'])==peak)})
    with (here/'period-profile.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(profile[0]),lineterminator='\n');w.writeheader();w.writerows(profile)
    top=max(.1,math.ceil(max(x['best_of_64_masks'] for x in profile)/.025)*.025)
    def x(p):return 44+(p-2)*10
    def y(v):return 242-v/top*160
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="320" viewBox="0 0 360 320" role="img" aria-labelledby="title desc">',f'<title id="title">Periodic IoC after ciphertext autokey: {r["mode"]} interruptions</title>','<desc id="desc">For each period from two through thirty, compare no selected interruptions with the maximum over all 64 F masks. These are observed scores, not separately tested probabilities.</desc>','<rect width="360" height="320" fill="#faf9f5"/>','<g font-family="Arial,sans-serif" fill="#263b45">',f'<text x="16" y="25" font-size="17">F interruptions: {r["mode"]}</text>','<text x="16" y="48" font-size="13">Pooled IoC · LP2-54–55</text>']
    for i in range(5):
        v=top*i/4
        svg.append(f'<path d="M44 {y(v):.2f}H324" stroke="#d8dcd9"/><text x="38" y="{y(v)+4:.2f}" text-anchor="end" font-size="12">{v:.3f}</text>')
    for p in [2,6,10,13,18,22,26,30]:svg.append(f'<text x="{x(p)}" y="261" text-anchor="middle" font-size="12">{p}</text>')
    for key,color,dash in [('no_interruptions','#8b6946','stroke-dasharray="4 3"'),('best_of_64_masks','#2d6076','')]:
        points=' '.join(f'{x(row["period"])},{y(row[key]):.2f}' for row in profile)
        svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2" {dash}/>')
    svg+=['<text x="184" y="280" text-anchor="middle" font-size="13">Period</text>','<path d="M18 297H40" stroke="#2d6076" stroke-width="2"/><text x="46" y="301" font-size="12">Best of 64 masks</text>','<path d="M186 297H208" stroke="#8b6946" stroke-width="2" stroke-dasharray="4 3"/><text x="214" y="301" font-size="12">No interruptions</text>','</g></svg>']
    (here/'period-profile.svg').write_text('\n'.join(svg)+'\n',encoding='utf-8',newline='\n')

if __name__=='__main__':main(Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent)
