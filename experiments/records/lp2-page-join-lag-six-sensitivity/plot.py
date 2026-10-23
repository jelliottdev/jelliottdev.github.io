"""Small-screen-readable contrast of page-break conventions."""
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
d=json.loads((HERE/'results.json').read_text(encoding='utf8'))
a,b=d['split_pages'],d['joined_pages']
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 310" role="img" aria-labelledby="t de">',
       '<title id="t">Two page-break rules yield similar lag-six counts</title>',
       '<desc id="de">Forcing all 55 page breaks to split words gives 1267 lag-six opportunities and 77 matches. Joining through rune-to-rune breaks gives 1290 opportunities and 80 matches. Both have 63 within-word adjacent doublets.</desc>',
       '<rect width="360" height="310" fill="#f7f8f9"/>',
       '<text x="16" y="29" font-family="system-ui,sans-serif" font-size="17" font-weight="650" fill="#24343d">Does joining pages change the test?</text>',
       '<text x="16" y="52" font-family="system-ui,sans-serif" font-size="11" fill="#536570">32 rune-to-rune edges; intended word breaks unknown.</text>',
       '<text x="16" y="92" font-family="system-ui,sans-serif" font-size="13" fill="#24343d">Word tokens</text>',
       f'<text x="340" y="92" text-anchor="end" font-family="system-ui,sans-serif" font-size="13" fill="#24343d">{a["tokens"]} → {b["tokens"]}</text>',
       '<path d="M16 106H344" stroke="#d2d9dc"/>',
       '<text x="16" y="136" font-family="system-ui,sans-serif" font-size="13" fill="#24343d">Six-rune opportunities</text>',
       f'<text x="340" y="136" text-anchor="end" font-family="system-ui,sans-serif" font-size="13" fill="#24343d">{a["lag_six_opportunities"]} → {b["lag_six_opportunities"]}</text>',
       '<path d="M16 150H344" stroke="#d2d9dc"/>',
       '<text x="16" y="180" font-family="system-ui,sans-serif" font-size="13" fill="#24343d">Formula matches</text>',
       f'<text x="340" y="180" text-anchor="end" font-family="system-ui,sans-serif" font-size="13" font-weight="650" fill="#24343d">{a["lag_six_matches"]} → {b["lag_six_matches"]}</text>',
       '<path d="M16 194H344" stroke="#d2d9dc"/>',
       '<text x="16" y="224" font-family="system-ui,sans-serif" font-size="13" fill="#24343d">Adjacent doublets</text>',
       f'<text x="340" y="224" text-anchor="end" font-family="system-ui,sans-serif" font-size="13" fill="#24343d">{a["adjacent_doublets"]} → {b["adjacent_doublets"]}</text>',
       '<path d="M16 238H344" stroke="#d2d9dc"/>',
       '<text x="16" y="270" font-family="system-ui,sans-serif" font-size="12" fill="#536570">Split pages → join pages</text>',
       '<text x="16" y="291" font-family="system-ui,sans-serif" font-size="11" fill="#536570">This bounds one parser choice, not the correct reading.</text>',
       '</svg>']
payload='\n'.join(parts)+'\n';out=HERE/'page-break-comparison.svg'
if args.check:assert out.read_text(encoding='utf8')==payload
else:out.write_text(payload,encoding='utf8')
print('Page-break figure checked.' if args.check else 'Page-break figure written.')
