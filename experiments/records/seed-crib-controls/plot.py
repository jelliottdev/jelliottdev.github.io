"""Plot every fixed crib length; ranges describe dependent control searches."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def render():
    report=HERE/'results.json'
    data=json.loads(report.read_bytes());audit=json.loads((HERE/'audit.json').read_bytes())
    assert hashlib.sha256(report.read_bytes()).hexdigest()==audit['report_sha256']
    groups=[('Correct crib · seed included',4),('Correct crib · seed outside range',2),
            ('Correct crib · wrong generator',6),('Incorrect first crib rune',12)]
    def group(c):
        if c['crib_condition']!='correct':return 3
        if c['generating_pair_in_search']:return 0
        return 1 if c['fixture'].split(':')[0]==c['search_generator'] else 2
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 720" role="img" aria-labelledby="title desc">',
        '<title id="title">How many seeds match the opening text?</title>',
        '<desc id="desc">All four control groups produce multiple matches at two runes. At four, eight, sixteen and thirty-two runes, included generating-pair searches retain one seed each and all other controls retain zero. Ranges describe these finite searches, not confidence intervals.</desc>',
        '<rect width="380" height="720" fill="white"/>',
        '<style>text{font:14px Arial,sans-serif;fill:#263c47}.title{font-size:18px;font-weight:bold}.group{font-weight:bold}</style>',
        '<text x="16" y="27" class="title">Seeds matching the opening text</text>',
        '<text x="16" y="51">Range across searches in each control group</text>',
        '<text x="16" y="73">Crib length</text><text x="132" y="73">Surviving seeds (minimum–maximum)</text>']
    for index,(label,count) in enumerate(groups):
        top=98+index*140
        parts.append(f'<text x="16" y="{top}" class="group">{label}</text>')
        parts.append(f'<text x="16" y="{top+18}">{count} searches per crib length</text>')
        for j,n in enumerate([2,4,8,16,32]):
            cells=[c for c in data['cells'] if group(c)==index and c['crib_length']==n]
            assert len(cells)==count
            values=[len(c['survivors']) for c in cells];lo=min(values);hi=max(values)
            y=top+37+j*19
            text=str(lo) if lo==hi else f'{lo}–{hi}'
            parts.extend([f'<text x="28" y="{y+4}">{n} runes</text>',
                f'<line x1="132" x2="{132+hi*15}" y1="{y}" y2="{y}" stroke="#d3dce1" stroke-width="9"/>',
                f'<line x1="{132+lo*15}" x2="{132+hi*15}" y1="{y}" y2="{y}" stroke="#315e72" stroke-width="5"/>',
                f'<circle cx="{132+lo*15}" cy="{y}" r="3" fill="#315e72"/>',
                f'<text x="315" y="{y+4}">{text}</text>'])
    parts.extend(['<text x="16" y="673">Each search tests 4,096 seeds under one generator.</text>',
        '<text x="16" y="695">Prefix agreement alone does not predict the rest.</text>','</svg>'])
    return '\n'.join(parts)+'\n'

if __name__=='__main__':
    (HERE/'prefix-matches.svg').write_text(render(),encoding='utf-8',newline='\n')
