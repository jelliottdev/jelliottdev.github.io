"""Plot saved word-length distributions. No new scoring or corpus selection.

python experiments/records/parallel-languages/distribution_figure.py --check
"""
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def figure(report):
    selected=[('Manuscript: rune units',report['target'],'#263b45')]
    for name,color in [('English','#315f73'),('Welsh','#99642d')]:
        selected.append((name+': letter units',next(x for x in report['modes']['letters']['ranking'] if x['language']==name),color))
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="700" viewBox="0 0 360 700" role="img" aria-labelledby="title desc">',
         '<title id="title">Where the length profiles differ</title>',
         '<desc id="desc">Three panels share a zero to thirty percent scale. Three-unit tokens are most common in the manuscript. Welsh has more one-letter words and fewer three-letter words. Lengths nine and above are combined for display only.</desc>',
         '<rect width="360" height="700" fill="#faf9f5"/><g font-family="Arial,sans-serif" fill="#263b45">',
         '<text x="14" y="27" font-size="19">Where the profiles differ</text>',
         '<text x="14" y="49" font-size="14">Percent of words; same scale in each panel</text>']
    for panel,(label,data,color) in enumerate(selected):
        top=78+panel*188; baseline=top+130
        values=data['histogram'][:8]+[sum(data['histogram'][8:])]
        assert sum(values)==data['tokens']
        out.append(f'<text x="14" y="{top}" font-size="16">{label}</text>')
        for tick in (0,10,20,30):
            y=baseline-tick*3.4
            out.append(f'<path d="M40 {y}H344" stroke="#d7dbda"/><text x="34" y="{y+4}" text-anchor="end" font-size="12">{tick}</text>')
        for i,count in enumerate(values):
            percent=100*count/data['tokens'];x=44+i*33;height=percent*3.4
            out.append(f'<rect x="{x}" y="{baseline-height:.3f}" width="23" height="{height:.3f}" fill="{color}"/>')
            out.append(f'<text x="{x+11.5}" y="{baseline-height-4:.3f}" text-anchor="middle" font-size="11">{percent:.1f}</text>')
            out.append(f'<text x="{x+11.5}" y="{baseline+18}" text-anchor="middle" font-size="13">{i+1 if i<8 else "9+"}</text>')
    out += ['<text x="14" y="645" font-size="14">Horizontal axis: counted units per word.</text>',
            '<text x="14" y="667" font-size="13">9+ is a display group, not the scoring bins.</text>',
            '<text x="14" y="688" font-size="13">Different units require a cipher assumption.</text></g></svg>']
    return '\n'.join(out)+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    result=figure(json.loads((HERE/'results.json').read_bytes()));path=HERE/'distributions.svg'
    if args.check:assert path.read_text(encoding='utf-8')==result
    else:path.write_text(result,encoding='utf-8',newline='\n')
    print('PASS: chart matches saved counts; display groups preserve all tokens')


if __name__=='__main__':main()
