"""Render saved full-pattern length counts; never run the corpus scanner."""
import argparse,json
from pathlib import Path
H=Path(__file__).resolve().parent
def render():
    rows=json.loads((H/'results.json').read_text(encoding='utf-8'))['real_patterns'][:3]
    labels=['Exact length','Within one rune','F-count interval']
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="600" height="680" viewBox="0 0 600 680" role="img" aria-labelledby="title desc">',
         '<title id="title">No full word-length pattern matched</title>',
         '<desc id="desc">Best compatible positions out of 2928: exact 593, symmetric slack-one 1445, directional F-count interval 664. These are lengths, not decoded words. 84 texts passed the unchanged source length gate.</desc>',
         '<rect width="600" height="680" fill="white"/>',
         '<g font-family="Arial, sans-serif" fill="#222">',
         '<text x="30" y="50" font-size="36" font-weight="bold">Matching word lengths</text>',
         '<text x="30" y="100" font-size="30">Each bar is out of 2,928 positions</text>',
         '<text x="30" y="150" font-size="30" fill="#555">84 eligible / 94 available texts</text>']
    for i,(row,label) in enumerate(zip(rows,labels)):
        y=225+i*100;w=540*row['count']/row['window']
        out.extend([f'<text x="30" y="{y}" font-size="32">{label}</text>',
                    f'<text x="570" y="{y}" font-size="32" text-anchor="end">{row["count"]:,} / 2,928</text>',
                    f'<rect x="30" y="{y+18}" width="540" height="40" fill="#ededed"/>',
                    f'<rect x="30" y="{y+18}" width="{w:.6f}" height="40" fill="#666"/>'])
    out.extend(['<rect x="30" y="530" width="28" height="28" fill="#666"/>',
                '<text x="75" y="555" font-size="30">Length-rule matches</text>',
                '<text x="30" y="612" font-size="32" font-weight="bold">No complete pattern match.</text>',
                '<text x="30" y="660" font-size="30" fill="#555">These are not decoded words.</text>',
                '</g></svg>'])
    return ('\n'.join(out)+'\n').encode('utf-8')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    raw=render();target=H/'length-matches.svg'
    if args.check:assert target.read_bytes()==raw;print('PASS: saved-count figure bytes agree; no scanner run.')
    else:target.write_bytes(raw)
