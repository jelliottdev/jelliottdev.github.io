"""Render source score-screen versus exact-recovery outcomes at phone width."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def render(data):
    controls=data['controls']
    no=[x for x in controls if x['mechanism']=='no-skip']
    skipped=[x for x in controls if x['mechanism']=='collision-skip']
    rows=[('No-skip plants',sum(x['above_source_bar'] for x in no),sum(x['plaintext_exact'] for x in no),18),
          ('Collision-skip plants',sum(x['above_source_bar'] for x in skipped),sum(x['plaintext_exact'] for x in skipped),18),
          ('Unsolved LP2 searches',data['real_above_source_bar'],None,54)]
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="316" viewBox="0 0 360 316" role="img" aria-labelledby="title desc">',
         '<title id="title">Score screen and exact recovery for the long-key beam</title>',
         '<desc id="desc">All 18 planted collision-skip cases pass the English-score bar, but none recover the exact plaintext. None of 54 manuscript searches passes the score bar.</desc>',
         '<rect width="360" height="316" fill="#f7f8fa"/>',
         '<text x="16" y="27" font-family="Arial,sans-serif" font-size="17" font-weight="700" fill="#202a33">A high score is not full recovery</text>',
         '<rect x="16" y="44" width="12" height="12" fill="#426780"/>',
         '<text x="35" y="55" font-family="Arial,sans-serif" font-size="13" fill="#34434f">Above English-score bar</text>',
         '<rect x="210" y="44" width="12" height="12" fill="#273a48"/>',
         '<text x="229" y="55" font-family="Arial,sans-serif" font-size="13" fill="#34434f">Exact text</text>']
    for i,(label,score_count,exact_count,total) in enumerate(rows):
        y=86+i*72
        out += [f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="14" font-weight="600" fill="#202a33">{label}</text>',
                f'<rect x="16" y="{y+12}" width="200" height="11" fill="#dce3e8"/>',
                f'<rect x="16" y="{y+12}" width="{round(200*score_count/total,2)}" height="11" fill="#426780"/>',
                f'<text x="226" y="{y+23}" font-family="Arial,sans-serif" font-size="14" fill="#202a33">Score {score_count}/{total}</text>']
        if exact_count is not None:
            out += [f'<rect x="16" y="{y+32}" width="200" height="11" fill="#dce3e8"/>',
                    f'<rect x="16" y="{y+32}" width="{round(200*exact_count/total,2)}" height="11" fill="#273a48"/>',
                    f'<text x="226" y="{y+43}" font-family="Arial,sans-serif" font-size="14" fill="#202a33">Exact {exact_count}/{total}</text>']
    out += ['<text x="16" y="301" font-family="Arial,sans-serif" font-size="13" fill="#45535f">Only the planted cases have a known exact answer.</text>','</svg>']
    return '\n'.join(out)+'\n'


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    data=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    output=render(data);path=HERE/'comparison.svg'
    if args.check:
        assert path.read_text(encoding='utf-8')==output
        print('PASS figure matches score and exact-recovery counts')
    else:
        path.write_text(output,encoding='utf-8',newline='\n');print(path)
