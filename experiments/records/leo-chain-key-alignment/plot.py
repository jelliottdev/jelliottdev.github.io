"""Small-screen figure of the source-selected section's full-grid control."""
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def svg():
    r=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    c=r['selected_section_control'];values=sorted(c['shuffle_maxima'])
    obs=c['observed_best'];med=values[len(values)//2]
    x=lambda v:36+(v-1.12)*3200
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 226" role="img" aria-labelledby="title desc">
<title id="title">Chain-key grid best score compared with 39 shuffled full searches</title>
<desc id="desc">The source-selected pages 54 to 55 best score is {obs:.3f}. The shuffled complete-search median is {med:.3f}; {c['exceedances']} of 39 shuffled searches matched or exceeded the observed score.</desc>
<rect width="320" height="226" fill="#f5f6f7"/>
<text x="16" y="28" font-size="17" font-family="Arial,sans-serif" font-weight="700" fill="#182b34">Chain-key search</text>
<text x="16" y="55" font-size="13" font-family="Arial,sans-serif" fill="#39515c">Pages 54–55 · best of 352,800 settings</text>
<line x1="36" y1="113" x2="275" y2="113" stroke="#6f7f87" stroke-width="2"/>
<line x1="{x(values[0]):.1f}" y1="113" x2="{x(values[-1]):.1f}" y2="113" stroke="#aab9c0" stroke-width="11"/>
<line x1="{x(med):.1f}" y1="94" x2="{x(med):.1f}" y2="132" stroke="#516e7d" stroke-width="3"/>
<circle cx="{x(obs):.1f}" cy="113" r="8" fill="#bb5e48" stroke="#fff" stroke-width="2"/>
<text x="36" y="147" font-size="13" font-family="Arial,sans-serif" fill="#536570">1.12</text>
<text x="155" y="147" font-size="13" font-family="Arial,sans-serif" fill="#536570">1.16</text>
<text x="253" y="147" font-size="13" font-family="Arial,sans-serif" fill="#536570">1.19</text>
<text x="16" y="180" font-size="14" font-family="Arial,sans-serif" font-weight="700" fill="#182b34">{c['exceedances']} of 39 shuffled searches</text>
<text x="16" y="200" font-size="13" font-family="Arial,sans-serif" fill="#39515c">matched or exceeded the observed best.</text>
</svg>'''


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args();path=HERE/'chain-key-control.svg';text=svg()
    if args.check:
        assert path.read_text(encoding='utf-8')==text
        print('PASS: control figure matches frozen results')
    else:path.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':main()
