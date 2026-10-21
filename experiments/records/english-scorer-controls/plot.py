"""Render every language and condition with identical axes and styling."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((ROOT/'experiments/plans/english-scorer-language-controls.json').read_bytes())
rows = json.loads((HERE/'results.json').read_bytes())['cells']
parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 1740" role="img" aria-labelledby="title desc">',
 '<title id="title">English scorer controls across eight languages</title>',
 '<desc id="desc">Six panels show all eight original scores per language and the range of 160 shuffled scores. The dashed line is the fixed acceptance threshold of minus 5.5. All panels share axes.</desc>',
 '<rect width="380" height="1740" fill="white"/>',
 '<style>text{font-family:Arial,sans-serif;fill:#243943;font-size:12px}.point{fill:#275d77;fill-opacity:.65}.range{stroke:#9ba5a9;stroke-width:4}</style>',
 '<text x="12" y="22" style="font-size:16px;font-weight:bold">Does the score accept known text?</text>',
 '<text x="12" y="44">Blue dots: originals · Gray: shuffled range</text>',
 '<text x="12" y="62">Dashed line: acceptance ≥ −5.5</text>']
def x(v): return 100+(v+10)*42
for panel,(mode,n) in enumerate((m,n) for m in plan['representations'] for n in plan['lengths']):
    top=90+panel*270
    label='A–Z only' if mode=='ascii' else 'Accents folded, then A–Z'
    parts.append(f'<text x="12" y="{top}" style="font-weight:bold">{label} · {n} letters</text>')
    for tick in (-10,-8,-6,-4):
        parts.append(f'<path d="M{x(tick)} {top+10}v205" stroke="#e1e5e7"/><text x="{x(tick)}" y="{top+234}" text-anchor="middle">{tick}</text>')
    parts.append(f'<path d="M{x(-5.5)} {top+10}v205" stroke="#705846" stroke-dasharray="4 3"/>')
    for i,(code,name) in enumerate(sorted(plan['languages'].items(),key=lambda p:p[1])):
        y=top+27+i*25
        cells=[r for r in rows if r['language']==code and r['representation']==mode and r['length']==n]
        controls=[s['score'] for r in cells for s in r['shuffles']]
        parts.append(f'<text x="12" y="{y+4}">{name}</text><path class="range" d="M{x(min(controls))} {y}H{x(max(controls))}"/>')
        for r in cells:
            assert -10<=r['score']<=-4
            parts.append(f'<circle class="point" cx="{x(r["score"])}" cy="{y}" r="3"/>')
        assert min(controls)>=-10 and max(controls)<=-4
parts.extend(['<text x="12" y="1730">Mean log₁₀ quadgram score · higher is better</text>','</svg>'])
(HERE/'comparison.svg').write_text('\n'.join(parts)+'\n',encoding='utf-8',newline='\n')
