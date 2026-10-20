"""Draw the search coverage from the saved plan and results; no new search."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
r=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
phases=sum(len(k['indices']) for k in p['keys'])
assert r['case_count']==len(p['pages'])*phases*len(p['signs'])
lines=[('Two recorded repeating keys', 'Welcome: 8 phases · Second koan: 13 phases'),
       (f'{phases} phases × {len(p["signs"])} directions', 'Subtract the key or add the key, modulo 29'),
       (f'{phases*len(p["signs"])} candidates per page', f'{len(p["pages"])} archived pages: LP2-00–55'),
       (f'{r["case_count"]:,} complete candidate streams', f'Each compared with {len(p["openings"])} fixed 12-rune openings'),
       (f'{r["comparison_count"]:,} exact opening comparisons', f'{r["matching_case_count"]} matches; every declared case completed')]
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 465" role="img" aria-labelledby="title desc"><title id="title">Known-key search coverage</title><desc id="desc">Two keys give 21 phases. Two arithmetic directions and 56 pages produce 2352 candidates. Nine exact known openings produce 21168 comparisons with zero matches. This does not rule out other plaintexts.</desc><rect width="360" height="465" fill="#faf9f5"/><g font-family="sans-serif" fill="#243c48"><text x="20" y="32" font-size="20">What the search covered</text>']
for i,(title,note) in enumerate(lines):
    y=72+i*69
    parts.append(f'<text x="20" y="{y}" font-size="17">{title}</text><text x="20" y="{y+23}" font-size="12.5">{note}</text>')
    if i<4:parts.append(f'<path d="M25 {y+32} v17 m-4 -4 l4 4 4 -4" stroke="#416879" fill="none"/>')
parts.append('<path d="M20 397 H340" stroke="#bec8ca"/><text x="20" y="421" font-size="13">No interruptions, later offsets or other keys.</text><text x="20" y="443" font-size="13">A different opening can still be valid plaintext.</text></g></svg>')
(HERE/'coverage.svg').write_text(''.join(parts)+'\n',encoding='utf-8',newline='\n')
