"""Mobile-readable source-marker alignment and an original-image evidence crop."""
import argparse
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
d=json.loads((HERE/'results.json').read_text(encoding='utf8'))
marked=[(r['page'],line) for r in d['regions'] for line in r['aligned'] if line['reviewed_marker']]
labels={"'":"apostrophe",'"':"quotation mark",'7':"number"}
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 365" role="img" aria-labelledby="t de">',
       '<title id="t">Marked lines align with wide spaces below</title>',
       '<desc id="de">Six selected lines containing an apostrophe, quotation mark or numeral are each followed by a 108–110 pixel gap. Twenty-eight unmarked lines in the same fixed regions have 73–75 pixel gaps.</desc>',
       '<rect width="360" height="365" fill="#f7f8f9"/>',
       '<text x="16" y="30" font-family="system-ui,sans-serif" font-size="17" font-weight="650" fill="#24343d">Mark on line → gap below</text>',
       '<text x="16" y="51" font-family="system-ui,sans-serif" font-size="11" fill="#536570">Six source-guided lines on five original pages.</text>']
for k,(page,line) in enumerate(marked):
    y=82+k*37
    marker=line['reviewed_marker'];name=labels.get(marker,'number' if marker.isdigit() else marker)
    parts += [f'<text x="16" y="{y}" font-family="system-ui,sans-serif" font-size="12" font-weight="650" fill="#24343d">{page.upper()} · line {line["line"]}</text>',
              f'<text x="176" y="{y}" font-family="system-ui,sans-serif" font-size="12" fill="#536570">{name}</text>',
              f'<text x="343" y="{y}" text-anchor="end" font-family="system-ui,sans-serif" font-size="12" font-weight="650" fill="#31566e">{line["gap_after"]} px</text>',
              f'<path d="M16 {y+10}H344" stroke="#d3dce0"/>']
parts += ['<text x="16" y="326" font-family="system-ui,sans-serif" font-size="12" fill="#24343d">28 unmarked lines: 73–75 px</text>',
          '<text x="16" y="348" font-family="system-ui,sans-serif" font-size="10" fill="#536570">LP2-35 apostrophe appears only in the reviewed text.</text>','</svg>']
svg='\n'.join(parts)+'\n';path=HERE/'mark-gap-alignment.svg'
crop=Image.open(ROOT/'images/lp2-35.jpg').crop((900,1200,1450,1400))
crop_path=HERE/'lp2-35-apostrophe.png'
if args.check:
    assert path.read_text(encoding='utf8')==svg
    assert Image.open(crop_path).tobytes()==crop.tobytes()
else:
    path.write_text(svg,encoding='utf8')
    crop.save(crop_path)
print('Alignment visual and original-image crop checked.' if args.check else 'Alignment visual and crop written.')
