"""Compact mobile SVG of full-book planted decoder power."""
import argparse
import json
from pathlib import Path

H=Path(__file__).resolve().parent
r=json.loads((H/'results.json').read_text(encoding='utf-8'))
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 332 298" role="img" aria-labelledby="t d" font-family="Arial, sans-serif">',
       '<title id="t">Known-key full-book recovery</title>',
       '<desc id="d">For a 12,956-rune synthetic message, both exact and permissive decoders recover over 99.8 percent with the correct key; wrong-key controls recover under five percent.</desc>',
       '<rect width="332" height="298" fill="#f8fafb"/>',
       '<text x="16" y="27" font-size="16" font-weight="700" fill="#172e3d">Known-key recovery</text>',
       '<text x="16" y="47" font-size="13" fill="#435865">12,956 runes · 3 correct / 1 wrong per rule</text>']
for idx,row in enumerate(r['modes']):
    y=75+idx*105
    label='Exact skip rule' if row['mode']=='repo_ms3' else 'Permissive drift rule'
    parts.append(f'<text x="16" y="{y}" font-size="14" font-weight="700" fill="#172e3d">{label}</text>')
    for offset,caption,value,color in ((13,'Correct key',row['median_correct_recovery'],'#255d78'),
                                        (51,'Wrong key',row['wrong_key_recovery'],'#9b7774')):
        yy=y+offset
        parts.append(f'<text x="16" y="{yy+11}" font-size="13" fill="#314958">{caption}</text>')
        parts.append(f'<rect x="117" y="{yy}" width="144" height="16" fill="#e3e9ec"/>')
        parts.append(f'<rect x="117" y="{yy}" width="{max(2,round(144*value))}" height="16" fill="{color}"/>')
        parts.append(f'<text x="267" y="{yy+13}" font-size="13" fill="#172e3d">{value*100:.2f}%</text>')
parts+=['<path d="M16 266H304" stroke="#c7d0d5"/>',
        '<text x="16" y="287" font-size="13" fill="#435865">Synthetic text; the key is supplied to decoder</text>',
        '</svg>']
svg='\n'.join(parts)+'\n'
parser=argparse.ArgumentParser()
parser.add_argument('--check',action='store_true')
args=parser.parse_args()
out=H/'full-book-power.svg'
if args.check:
    assert svg==out.read_text(encoding='utf-8')
else:
    out.write_text(svg,encoding='utf-8',newline='\n')
print('PASS plot' if args.check else 'wrote SVG')
