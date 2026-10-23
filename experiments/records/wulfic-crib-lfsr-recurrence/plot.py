"""Compact mobile-first result graphic; no bitmap or remote assets."""
import json
from pathlib import Path

H = Path(__file__).resolve().parent
r = json.loads((H / 'results.json').read_text(encoding='utf-8'))
power = json.loads((H / 'power-results.json').read_text(encoding='utf-8'))
grid = json.loads((H / 'power-grid-results.json').read_text(encoding='utf-8'))
ablation = {(x['parser'],x['phase']):x['correct_of_128_retained']
            for x in r['controls']['ablation']}
null = sorted(x for x in r['shared_null_maxima'] if x is not None)
obs = r['observed_global_best']['score'] if r['observed_global_best'] else None
median = null[len(null)//2] if null else None
high = null[-1] if null else None
maximum = max([x for x in (obs,high) if x is not None],default=1)

parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 420" '
         'role="img" aria-labelledby="t d" font-family="Arial, sans-serif">',
         '<title id="t">Crib-key corrections and manuscript score</title>',
         '<desc id="d">Four planted-message tests isolate missing J runes and wrong key phase. '
         'The best manuscript score is compared with shuffled-page searches. A post-result known-reading plant leads all 11 mixed-grid pages in 12 of 12 cases.</desc>',
         '<rect width="320" height="420" fill="#f8fafb"/>',
         '<text x="16" y="27" font-size="16" font-weight="700" fill="#172e3d">Two fixes on a known message</text>',
         '<text x="96" y="54" font-size="13" fill="#435865">Key starts at 0</text>',
         '<text x="214" y="54" font-size="13" fill="#435865">At the crib</text>']
for y, parser, label in ((66,'source','Drops J'),(118,'canonical','Keeps J')):
    parts.append(f'<text x="15" y="{y+23}" font-size="13" fill="#293e4c">{label}</text>')
    for x,phase in ((96,'source'),(214,'corrected')):
        count = ablation[(parser,phase)]
        fill = '#d6e1e6' if count != 128 else '#c4e5d7'
        parts.append(f'<rect x="{x}" y="{y}" width="96" height="42" rx="5" fill="{fill}"/>')
        parts.append(f'<text x="{x+48}" y="{y+27}" text-anchor="middle" font-size="18" '
                     f'font-weight="700" fill="#173647">{count}/128</text>')
parts.extend(['<text x="16" y="179" font-size="13" fill="#435865">Runes recovered after the planted crib</text>',
              '<path d="M16 195H304" stroke="#c7d0d5"/>',
              '<text x="16" y="221" font-size="16" font-weight="700" fill="#172e3d">On 11 LP2 pages</text>'])
for y,label,val,color in ((238,'Best found',obs,'#255d78'),
                          (275,'Shuffle middle',median,'#8298a3'),
                          (312,'Shuffle highest',high,'#607f8e')):
    parts.append(f'<text x="16" y="{y+13}" font-size="13" fill="#2c424f">{label}</text>')
    if val is None:
        parts.append(f'<text x="191" y="{y+13}" font-size="13" fill="#2c424f">none</text>')
    else:
        width = max(2,round(105*val/maximum))
        parts.append(f'<rect x="157" y="{y}" width="{width}" height="17" fill="{color}"/>')
        parts.append(f'<text x="272" y="{y+14}" font-size="13" fill="#172e3d">{val}</text>')
parts.extend(['<path d="M16 345H304" stroke="#c7d0d5"/>',
              '<text x="16" y="369" font-size="15" font-weight="700" fill="#172e3d">Known-reading plant</text>',
              f'<text x="16" y="392" font-size="14" fill="#172e3d">Score {power["known_continuation_score"]}; {sum(x["global_rank_one"] for x in grid["rows"])}/12 lead mixed grid</text>',
              '<text x="16" y="410" font-size="13" fill="#435865">Post-result; different page length</text>',
              '</svg>'])
(H / 'result.svg').write_text('\n'.join(parts)+'\n',encoding='utf-8',newline='\n')
print('result.svg written, observed',obs,'shuffle high',high)
