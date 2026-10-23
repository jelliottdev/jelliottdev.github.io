"""Draw the complete matrix-family comparison for a narrow viewport."""
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
LABELS=[('M1_1033','1033 square'),('M2_3301','3301 square'),
        ('M3_4x4','4×4 source'),('M1_phi','1033 variant'),
        ('M2_phi','3301 variant'),('M3_phi','4×4 variant'),
        ('M3_image_cell','4×4 corrected cell')]


def render(data):
    best={name:max(x['score'] for x in data['cases'] if x['group']==name) for name,_ in LABELS}
    # Scores run from -8.0 to the source's declared -5.0 screen.
    sx=lambda score: 154 + max(0,min(1,(score+8)/3))*126
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="320" height="413" viewBox="0 0 320 413" role="img" aria-labelledby="title desc">',
         '<title id="title">Source Hill matrices: best English score</title>',
         '<desc id="desc">All six source matrices and the one corrected-grid variant remain below the source score bar of minus five. The score is selected across 56 targets and four operations per matrix.</desc>',
         '<rect width="320" height="413" fill="#f5f7f9"/>',
         '<text x="12" y="27" font-family="Arial,sans-serif" font-size="17" font-weight="700" fill="#202a33">Can the book matrices read LP2?</text>',
         '<text x="12" y="49" font-family="Arial,sans-serif" font-size="13" fill="#46545f">Best per matrix · higher is more English-like</text>',
         '<line x1="280" y1="76" x2="280" y2="341" stroke="#9b584d" stroke-width="2" stroke-dasharray="4 3"/>',
         '<text x="236" y="71" font-family="Arial,sans-serif" font-size="13" fill="#87433d">flag −5.0</text>']
    for i,(name,label) in enumerate(LABELS):
        y=97+i*37
        x=sx(best[name]);fill='#345f7b' if name!='M3_image_cell' else '#4b6980'
        out += [f'<text x="12" y="{y}" font-family="Arial,sans-serif" font-size="13" fill="#202a33">{label}</text>',
                f'<line x1="154" y1="{y-5}" x2="280" y2="{y-5}" stroke="#dce4e9" stroke-width="10"/>',
                f'<line x1="154" y1="{y-5}" x2="{x:.1f}" y2="{y-5}" stroke="{fill}" stroke-width="10"/>',
                f'<text x="{max(154,x-4):.1f}" y="{y+14}" text-anchor="end" font-family="Arial,sans-serif" font-size="13" fill="#263946">{best[name]:.3f}</text>']
    out += ['<line x1="12" y1="367" x2="308" y2="367" stroke="#cbd4db"/>',
            '<text x="12" y="388" font-family="Arial,sans-serif" font-size="13" fill="#46545f">LP2-15 cell: 1820 in image, 820 in source.</text>',
            '<text x="12" y="405" font-family="Arial,sans-serif" font-size="13" fill="#46545f">No tested output crossed the source’s English flag.</text>',
            '</svg>']
    return '\n'.join(out)+'\n'


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    svg=render(json.loads((HERE/'results.json').read_text(encoding='utf-8')))
    path=HERE/'comparison.svg'
    if a.check:
        assert path.read_text(encoding='utf-8')==svg
        print('PASS figure matches saved matrix scores')
    else:
        path.write_text(svg,encoding='utf-8',newline='\n')
        print(path)
