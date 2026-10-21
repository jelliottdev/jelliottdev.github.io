"""Draw the audited unchanged-rune counts, keeping causes separate."""
from pathlib import Path
import json
from audit_reading_fixed_points import audit

ROOT=Path(__file__).resolve().parents[1]

def render():
    report=json.loads((ROOT/'exports/reading-fixed-points.json').read_bytes())
    assert report==audit(),'Saved audit no longer matches source traces'
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 480" role="img" aria-labelledby="title desc">',
        '<title id="title">Unchanged does not mean skipped</title>',
        '<desc id="desc">Counts of unchanged rune positions: Warning 2 ordinary fixed points; Welcome 11 interruptions; first koan 34 ordinary fixed points; second koan 98 ordinary fixed points and 2 interruptions. Total 147 unchanged, including only 13 interruptions.</desc>',
        '<rect width="380" height="480" fill="white"/>',
        '<style>text{font:14px Arial,sans-serif;fill:#25343a}.small{font-size:12px}</style>',
        '<text x="18" y="27">Unchanged does not mean skipped</text>',
        '<text x="18" y="51" class="small">Aligned rune positions in four known LP1 readings</text>']
    labels=['Warning','Welcome','First koan','Second koan']
    for i,(row,label) in enumerate(zip(report['summaries'],labels)):
        y=82+76*i;n=row['ordinary_fixed_points'];s=row['recorded_interruptions']
        parts += [f'<text x="18" y="{y}">{label}</text>',
            f'<text x="362" y="{y}" text-anchor="end" class="small">{row["unchanged_indices"]} / {row["runes"]} runes unchanged</text>',
            f'<rect x="18" y="{y+12}" width="{3.44*n:.2f}" height="16" fill="#42687b"/>',
            f'<rect x="{18+3.44*n:.2f}" y="{y+12}" width="{3.44*s:.2f}" height="16" fill="#a46f2e"/>',
            f'<text x="18" y="{y+48}" class="small">{n} ordinary fixed points + {s} interruptions</text>']
    parts += ['<text x="18" y="384" class="small">Bar lengths count positions; shared scale: 0–100.</text>',
        '<rect x="18" y="401" width="12" height="12" fill="#42687b"/><text x="37" y="412">Ordinary cipher arithmetic: 134</text>',
        '<rect x="18" y="424" width="12" height="12" fill="#a46f2e"/><text x="37" y="435">Recorded interruptions: 13</text>',
        '<text x="18" y="464" class="small">147 unchanged positions among 1,796 runes.</text>','</svg>']
    return '\n'.join(parts)+'\n'

if __name__=='__main__':
    (ROOT/'exports/figures/reading-fixed-points.svg').write_text(render(),encoding='utf-8',newline='\n')
