"""Render the first six actual source positions of one saved column route."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
page=next(p for p in r['pages'] if p['page']=='lp2-31')
case=next(c for c in page['cases'] if c['axis']=='column' and not any(c[k] for k in ('outer_reverse','inner_reverse','alternating')))
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 430" role="img" aria-labelledby="title desc"><title id="title">LP2-31 column-first source trace</title><desc id="desc">First six actual output positions from a saved column-first route. Each points to the first rune of the next archived row. Full routes preserve every source position.</desc><rect width="360" height="430" fill="#faf9f5"/><g font-family="sans-serif" fill="#243c48"><text x="20" y="30" font-size="20">LP2-31: column-first route</text><text x="20" y="55" font-size="13">Down each column, then move right</text><text x="20" y="86" font-size="13">Step</text><text x="90" y="86" font-size="13">Source line : rune</text><text x="273" y="86" font-size="13">Index</text>']
for i,ordinal in enumerate(case['source_ordinals'][:6],1):
    source=page['source_positions'][ordinal];y=120+(i-1)*37
    parts.append(f'<path d="M20 {y+13} H330" stroke="#dce0df"/><text x="20" y="{y}" font-size="16">{i}</text><text x="90" y="{y}" font-size="16">{source["line"]} : {source["rune_position"]}</text><text x="273" y="{y}" font-size="16">{source["index"]}</text>')
parts.append(f'<text x="20" y="350" font-size="13">Full route: {len(case["source_ordinals"])} positions, each used once</text><text x="20" y="376" font-size="13">Rows are left-aligned by rune ordinal.</text><text x="20" y="402" font-size="13">Rune indices use alphabet positions 0–28.</text></g></svg>')
(HERE/'source-trace.svg').write_text(''.join(parts)+'\n',encoding='utf-8',newline='\n')
