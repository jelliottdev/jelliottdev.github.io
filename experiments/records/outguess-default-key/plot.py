"""Draw a coverage map from the saved extraction report; no extraction occurs."""
import json
from pathlib import Path
from html import escape
HERE=Path(__file__).resolve().parent
rows=json.loads((HERE/'results/report.json').read_text(encoding='utf-8'))['records']
lookup={r['image']:r for r in rows}
colors={'control-match':'#326958','candidate-output':'#a35328','no-successful-retrieval':'#616b73','timeout':'#9c3034','control-failed':'#9c3034'}
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 740" role="img" aria-labelledby="title desc"><title id="title">Default-key OutGuess coverage</title><desc id="desc">Each numbered cell is an original manuscript image. Green means the extracted bytes matched a known control, orange means unverified candidate bytes, gray means no successful retrieval, and red means a control failure or timeout. This does not test other keys or methods.</desc><rect width="360" height="740" fill="#faf9f5"/><g font-family="sans-serif" fill="#243c48"><text x="20" y="30" font-size="20">Default-key extraction coverage</text><text x="20" y="53" font-size="13">One retrieval per original JPEG</text>']
for prefix,count,top in [('lp1',17,94),('lp2',58,252)]:
    parts.append(f'<text x="20" y="{top}" font-size="17">{prefix.upper()} · zero-based page numbers</text>')
    for i in range(count):
        r=lookup[f'{prefix}-{i:02}'];x=20+(i%8)*40;y=top+15+(i//8)*34
        parts.append(f'<g><title>{escape(r["image"]+": "+r["status"])}</title><rect x="{x}" y="{y}" width="34" height="27" rx="2" fill="{('#9c3034' if r['returncode'] not in (0,1) else colors[r['status']])}"/><text x="{x+17}" y="{y+19}" text-anchor="middle" font-size="14" fill="white">{i:02}</text></g>')
for i,name in enumerate(['opening-2014','1033']):
    r=lookup[name];y=566+i*26
    parts.append(f'<rect x="20" y="{y-13}" width="14" height="14" fill="{('#9c3034' if r['returncode'] not in (0,1) else colors[r['status']])}"/><text x="42" y="{y}" font-size="14">{name}: {r["status"]}</text>')
parts.append('<text x="20" y="626" font-size="13">Green: known bytes reproduced</text><text x="20" y="646" font-size="13">Orange: unverified output bytes</text><text x="20" y="666" font-size="13">Gray: retrieval rejected (exit 1)</text><text x="20" y="686" font-size="13">Red: abnormal exit; unresolved tool failure</text><text x="20" y="720" font-size="13">No cell establishes absence of hidden data.</text></g></svg>')
(HERE/'coverage.svg').write_text(''.join(parts)+'\n',encoding='utf-8',newline='\n')
