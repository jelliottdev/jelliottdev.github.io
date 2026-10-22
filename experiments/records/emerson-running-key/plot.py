"""Render selected-window and held-out running-key scores."""
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def figure(data):
    left,right,low,high=170,740,-8.2,-3.4
    def x(value):return left+(value-low)/(high-low)*(right-left)
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="780" height="440" viewBox="0 0 780 440" role="img" aria-labelledby="title desc">',
           '<title id="title">Emerson running-key search and continuation scores</title>',
           '<desc id="desc">Best 96-rune Emerson openings for three LP2 pages score near maxima from eight complete shuffled-source searches. Their 96-rune continuations remain much lower than the planted known-reading control.</desc>',
           '<rect width="780" height="440" fill="#faf9f5"/>',
           '<g font-family="Arial,sans-serif" fill="#263b45">',
           '<text x="20" y="31" font-size="21">A high opening must continue</text>',
           '<text x="20" y="53" font-size="13">Emerson running key · 43,325 offsets per search · higher score is better</text>']
    for tick in (-8,-7,-6,-5,-4):
        xx=x(tick)
        parts += [f'<path d="M{xx:.1f} 75V356" stroke="#d9dddb"/>',
                  f'<text x="{xx:.1f}" y="376" font-size="12" text-anchor="middle">{tick}</text>']
    y=89
    for target in data['targets']:
        original=target['searches'][0]['top_five'][0]
        shuffled=[row['top_five'][0] for row in target['searches'][1:]]
        for label,field in [('selected 96','selection_score'),('next 96','continuation_score')]:
            values=[row[field] for row in shuffled]
            a,b=min(values),max(values)
            xx=x(original[field])
            parts += [f'<text x="20" y="{y+5}" font-size="13">{target["page"].upper()} · {label}</text>',
                      f'<path d="M{x(a):.1f} {y}H{x(b):.1f}" stroke="#bb805d" stroke-width="8" stroke-linecap="round"/>',
                      f'<circle cx="{xx:.1f}" cy="{y}" r="6" fill="#315f73" stroke="#faf9f5" stroke-width="2"/>']
            y+=34
        y+=10
    planted=data['planted_control']
    for label,field in [('selected 96','known_opening_score'),('next 96','known_continuation_score')]:
        parts += [f'<text x="20" y="{y+5}" font-size="13">LP1 plant · {label}</text>',
                  f'<circle cx="{x(planted[field]):.1f}" cy="{y}" r="6" fill="#315f73"/>']
        y+=34
    parts += ['<text x="455" y="399" font-size="12" text-anchor="middle">Mean English quadgram log₁₀ score of canonical rune labels</text>',
              '<path d="M28 417H62" stroke="#bb805d" stroke-width="8" stroke-linecap="round"/><text x="70" y="422" font-size="12">Range of 8 shuffled-source search maxima</text>',
              '<circle cx="405" cy="417" r="6" fill="#315f73"/><text x="418" y="422" font-size="12">Archived Emerson or planted control</text>',
              '</g></svg>']
    return '\n'.join(parts)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    content=figure(json.loads((HERE/'results.json').read_text(encoding='utf-8')))
    output=HERE/'search-scores.svg'
    if args.check:
        assert output.read_text(encoding='utf-8')==content
        print('PASS: running-key comparison figure reproduces')
    else:
        output.write_text(content,encoding='utf-8',newline='\n')
        print(output)


if __name__=='__main__':main()
