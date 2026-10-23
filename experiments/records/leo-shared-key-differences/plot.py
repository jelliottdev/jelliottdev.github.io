"""Draw a compact source-audit figure from frozen numeric results."""
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def draw():
    main=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    follow=json.loads((HERE/'followup-results.json').read_text(encoding='utf-8'))
    chosen=follow['observed']['z']
    vals=sorted(follow['shuffle_maxima'])
    median=vals[len(vals)//2]
    lo,hi=vals[0],vals[-1]
    scale=lambda z:38+(z-4)*56
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 270" role="img" aria-labelledby="title desc">
<title id="title">Cross-section difference peak against the same complete search on shuffled sections</title>
<desc id="desc">The strongest cross-section score is {chosen:.2f}. It is close to the shuffle median {median:.2f}; {follow['shuffle_exceedances']} of 99 shuffled complete searches have a score at least as high. The strongest all-pair score, {main['lp2']['global_max']['z']:.2f}, comes instead from adjacent runes in the same section.</desc>
<rect width="320" height="270" fill="#f5f6f7"/>
<text x="16" y="28" fill="#1c2830" font-size="17" font-weight="700" font-family="Arial,sans-serif">Shared-key alignment</text>
<text x="16" y="58" fill="#334751" font-size="13" font-family="Arial,sans-serif">Best distinct-section score: {chosen:.2f}</text>
<text x="16" y="78" fill="#334751" font-size="13" font-family="Arial,sans-serif">Shuffle median: {median:.2f}</text>
<line x1="38" y1="148" x2="290" y2="148" stroke="#687983" stroke-width="2"/>
<line x1="{scale(lo):.1f}" y1="148" x2="{scale(hi):.1f}" y2="148" stroke="#9daeb9" stroke-width="11"/>
<line x1="{scale(median):.1f}" y1="128" x2="{scale(median):.1f}" y2="168" stroke="#516e7d" stroke-width="3"/>
<circle cx="{scale(chosen):.1f}" cy="148" r="8" fill="#bb5e48" stroke="#fff" stroke-width="2"/>
<text x="36" y="184" fill="#536570" font-size="13" font-family="Arial,sans-serif">4</text>
<text x="149" y="184" fill="#536570" font-size="13" font-family="Arial,sans-serif">6</text>
<text x="261" y="184" fill="#536570" font-size="13" font-family="Arial,sans-serif">8</text>
<text x="16" y="218" fill="#1c2830" font-size="14" font-weight="700" font-family="Arial,sans-serif">{follow['shuffle_exceedances']} of 99 shuffled searches</text>
<text x="16" y="238" fill="#334751" font-size="13" font-family="Arial,sans-serif">matched or exceeded the observed peak.</text>
<text x="16" y="257" fill="#536570" font-size="12" font-family="Arial,sans-serif">Post-observation diagnostic · source-defined score</text>
</svg>'''


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    target=HERE/'cross-section-control.svg'
    svg=draw()
    if args.check:
        assert target.read_text(encoding='utf-8')==svg
        print('PASS: compact figure matches numeric results')
    else:
        target.write_text(svg,encoding='utf-8',newline='\n')


if __name__=='__main__':
    main()
