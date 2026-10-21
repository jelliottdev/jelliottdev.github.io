"""All-section search-maximum figures and full grouped CSV, without result selection."""
import csv
import hashlib
import json
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent
report=json.loads((HERE/'results.json').read_bytes())
audit=json.loads((HERE/'audit.json').read_bytes())
assert audit['report_sha256']==hashlib.sha256((HERE/'results.json').read_bytes()).hexdigest()
assert audit['wrong_key_scores_checked']==147456
records=report['paired_searches'];sections=list(dict.fromkeys(p['section'] for p in records))
budgets=[1,4,16,64,256];rows=[]
for section in sections:
    selected=[p for p in records if p['section']==section];assert len(selected)==32
    for budget in budgets:
        for condition in ('null','key-absent','key-included'):
            values=[];accepted=0;exact=0
            for p in selected:
                source=p['null' if condition=='null' else 'positive']['searches']
                r=next(v for v in source if v['budget']==budget)
                winner=r['included_winner' if condition=='key-included' else 'winner']
                values.append(winner['score'])
                accepted+=r['included_score_accepted' if condition=='key-included' else 'score_accepted']
                if condition!='null':exact+=winner['matches_reference']
            rows.append({'section':section,'rune_count':selected[0]['length'],'condition':condition,
                         'wrong_keys':budget,'candidate_count':budget+int(condition=='key-included'),
                         'searches':32,'minimum':min(values),'median':statistics.median(values),
                         'maximum':max(values),'accepted':accepted,
                         'exact_recovery':exact if condition!='null' else ''})
assert len(rows)==135
with (HERE/'summary.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
styles=[('null','#315f76',-6),('key-absent','#9b663c',0),('key-included','#4c7457',6)]
for group in range(3):
    svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 1050" role="img" aria-labelledby="t d">',
         '<title id="t">Best score from complete nested key searches</title>',
         '<desc id="d">Three source sections, each with five search budgets. Vertical ranges show minimum to maximum across 32 searches; dots show medians. Null, positive with key absent, and positive with key included share axes. Ranges are not confidence intervals.</desc>',
         '<rect width="380" height="1050" fill="white"/><style>text{font:12px Arial,sans-serif;fill:#293d47}</style>',
         '<text x="12" y="23" style="font-size:16px;font-weight:bold">Best score from each whole search</text>']
    for i,(condition,color,_) in enumerate(styles):
        title={'null':'Null ciphertext','key-absent':'Positive · true key absent','key-included':'Positive · true key included'}[condition]
        y=45+i*19
        svg.append(f'<circle cx="18" cy="{y-4}" r="3" fill="{color}"/><text x="30" y="{y}">{title}</text>')
    svg.append('<text x="12" y="103">Range and median of 32 searches · fixed threshold −5.5</text>')
    for panel,section in enumerate(sections[group*3:group*3+3]):
        top=135+panel*295
        length=next(r['rune_count'] for r in rows if r['section']==section)
        name=section.upper() if section.startswith('lp2') else section.replace('-',' ').title()
        svg.append(f'<text x="12" y="{top}" style="font-weight:bold">{name} · {length} runes</text>')
        def y(v):return top+220-(v+8.5)*40
        for tick in (-8,-7,-6,-5,-4):
            svg.append(f'<path d="M48 {y(tick)}H350" stroke="#e2e6e8"/><text x="39" y="{y(tick)+4}" text-anchor="end">{tick}</text>')
        svg.append(f'<path d="M48 {y(-5.5)}H350" stroke="#717171" stroke-dasharray="4 3"/>')
        for j,budget in enumerate(budgets):
            x=65+j*67
            svg.append(f'<text x="{x}" y="{top+244}" text-anchor="middle">{budget}</text>')
            for condition,color,offset in styles:
                r=next(v for v in rows if v['section']==section and v['wrong_keys']==budget and v['condition']==condition)
                assert -8.5<=r['minimum']<=r['maximum']<=-3.5
                svg.append(f'<path d="M{x+offset} {y(r["minimum"])}V{y(r["maximum"])}" stroke="{color}" stroke-width="2"/><circle cx="{x+offset}" cy="{y(r["median"])}" r="3" fill="{color}"/>')
        svg.append(f'<text x="48" y="{top+265}">Wrong-key budget (included arm adds one true key)</text>')
    svg+=['<text x="12" y="1037">Observed ranges, not confidence intervals or probabilities.</text>','</svg>']
    (HERE/f'maxima-{group+1}.svg').write_text('\n'.join(svg)+'\n',encoding='utf-8',newline='\n')
print('Rendered every source section; 135 grouped rows include all conditions and budgets')
