"""Compact section-selection diagnostic from fixed results."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
labels={'p0-2':'00–02','p3-7':'03–07','p8-14':'08–14','p15-22':'15–22',
        'p23-26':'23–26','p27-32':'27–32','p33-39':'33–39',
        'p40-53':'40–53','p54-55':'54–55'}
rows=list(r['sections'].items())
out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 444" role="img" aria-labelledby="title desc">',
     '<title id="title">Whole-grid shuffle comparison by LP2 section</title>',
     '<desc id="desc">The lowest conditional tail is four percent on pages 00 to 02. Across nine section choices, the simple adjusted bound is thirty-six percent.</desc>',
     '<rect width="340" height="444" fill="#f3f5f6"/>',
     '<text x="16" y="29" font-family="Arial,sans-serif" font-size="17" font-weight="bold" fill="#26343c">Sequence-key grid: selected maxima</text>',
     '<text x="16" y="51" font-family="Arial,sans-serif" font-size="14" fill="#52616a">Plus-one tail against 99 shuffles</text>']
for i,(name,row) in enumerate(rows):
    y=82+36*i
    percent=100*row['selected_grid_tail']
    width=177*percent/100
    color='#315d79' if i==0 else '#7a909e'
    out.extend([f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="15" fill="#26343c">{labels[name]}</text>',
                f'<rect x="87" y="{y-14}" width="177" height="17" fill="#e2e7e9"/>',
                f'<rect x="87" y="{y-14}" width="{width:.2f}" height="17" fill="{color}"/>',
                f'<text x="273" y="{y}" font-family="Arial,sans-serif" font-size="15" fill="#26343c">{percent:.0f}%</text>'])
out.extend(['<path d="M16 405H324" stroke="#cbd4d9"/>',
            '<text x="16" y="427" font-family="Arial,sans-serif" font-size="14" fill="#394951">Best 4%; nine-section bound 36%</text>',
            '</svg>'])
(HERE/'section-key-grid.svg').write_text('\n'.join(out)+'\n',encoding='utf-8')
print('wrote section-key-grid.svg')
