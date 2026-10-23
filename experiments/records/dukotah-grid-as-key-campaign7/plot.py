"""Generate the compact score comparison from the saved source replay."""
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
LABELS=[('A2_tokenpad','Grid bytes'),('A2_altbase','Other bases'),('B2_onion_xor','Onion XOR')]


def svg():
    data=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    rows=[]
    for j,(key,label) in enumerate(LABELS):
        value=data['groups'][key]['best']['score']
        y=84+j*49
        end=134+(value+7.5)*72
        rows.append(f'<text x="16" y="{y}" font-size="14">{label}</text>'
                    f'<rect x="134" y="{y-15}" width="{end-134:.1f}" height="18" fill="#285c73"/>'
                    f'<text x="{end+5:.1f}" y="{y}" font-size="14">{value:.3f}</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 238" '
            'role="img" aria-labelledby="title desc" style="font-family:Arial,sans-serif">'
            '<title id="title">Best English scores by byte-key reading</title>'
            '<desc id="desc">The best of three source searches ranges from minus 6.745 to minus 6.597. '
            'All are below the source flag threshold, minus 5.2.</desc>'
            '<rect width="320" height="238" fill="#f4f6f7"/>'
            '<text x="16" y="28" font-size="17" font-weight="700" fill="#1f2932">Grid bytes as keys</text>'
            '<text x="16" y="49" font-size="13" fill="#37444d">Best English score · higher is better</text>'
            '<line x1="300" y1="60" x2="300" y2="184" stroke="#9c3e40" stroke-width="2"/>'
            +''.join(rows)+
            '<text x="16" y="210" font-size="13" fill="#37444d">No score reached the −5.2 flag line.</text>'
            '<text x="16" y="229" font-size="12" fill="#52616a">14,784 source-defined cases · 0 flags</text>'
            '</svg>\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    path=HERE/'comparison.svg'
    content=svg()
    if a.check:
        assert path.read_text(encoding='utf-8')==content
        print('PASS: chart matches results')
    else:
        path.write_text(content,encoding='utf-8',newline='\n')
