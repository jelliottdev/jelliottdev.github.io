"""Render the explicitly exploratory whole-key-search calibration."""
import json
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'calibration-results.json').read_bytes());hist=Counter(r['null_global_maxima']);scale=130/max(hist.values());left=52;unit=13.5;base=352
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="580" height="570" viewBox="0 0 580 570" role="img" aria-label="Observed dictionary maximum126 sits within128 shuffled-page full-search maxima;90 controls are at least as high. All45 planted Warning scoring controls rank the true map first. Post-target exploratory calibration.">','<rect width="580" height="570" fill="white"/>','<g font-family="Arial,sans-serif" fill="#17212b">','<text x="24" y="35" font-size="24">Keyword columns: raw score calibration</text>','<text x="24" y="75" font-size="20">45 keyword labels · 43 distinct column orders</text>','<text x="24" y="113" font-size="22">Observed maximum: 126 / 2,776 word slots</text>','<text x="24" y="155" font-size="20">128 shared-page shuffled full-search maxima</text>']
for value,n in sorted(hist.items()):
 x=left+(value-112)*unit;height=n*scale;parts.append(f'<rect x="{x-5:.2f}" y="{base-height:.2f}" width="10" height="{height:.2f}" fill="#aeb8c2"/>')
x=left+(126-112)*unit
parts += [f'<line x1="{x}" x2="{x}" y1="192" y2="{base}" stroke="#263a4c" stroke-width="3"/>',f'<text x="{x-50}" y="184" font-size="20">Observed 126</text>',f'<line x1="{left}" x2="552" y1="{base}" y2="{base}" stroke="#788793"/>']
for v in [112,120,128,136,144]:parts.append(f'<text x="{left+(v-112)*unit-16}" y="382" font-size="20">{v}</text>')
parts += ['<text x="24" y="422" font-size="20">90 / 128 shuffled maxima are at least 126.</text>','<text x="24" y="462" font-size="20">Warning: all 45 planted keys rank the true map first.</text>','<text x="24" y="492" font-size="20">Its known spelling scores 30 / 45 word slots.</text>','<line x1="24" x2="556" y1="513" y2="513" stroke="#c4ccd4"/>','<text x="24" y="543" font-size="20">Post-target calibration; no prospective claim.</text>','</g></svg>']
(HERE/'column-order.svg').write_text(''.join(parts)+'\n',encoding='utf8')
