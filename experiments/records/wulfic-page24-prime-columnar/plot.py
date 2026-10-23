"""Phone-readable distribution of the complete-search shuffle maxima."""
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE/'comparison.svg'
BINS=((0,199,'Below 200'),(200,249,'200–249'),(250,299,'250–299'),
      (300,349,'300–349'),(350,100000,'350 or more'))


def figure():
    result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    values=[row['max_trigram_score'] for row in result['null']]
    observed=result['stage_two']['ranked'][0]['trigram_score']
    bins=[sum(low<=value<=high for value in values) for low,high,_ in BINS]
    assert sum(bins)==len(values)==256
    parts=[
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 350 326">',
        '<title id="title">The best manuscript trigram score compared with 256 full-search shuffles</title>',
        f'<desc id="desc">The manuscript best is {observed}. In {result["null_ge_observed"]} of 256 shuffled-page searches, the best score was at least this high.</desc>',
        '<rect width="350" height="326" fill="#fff"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#26343c;font-size:13px}.title{font-size:18px;font-weight:700}.strong{font-size:14px;font-weight:700}.muted{fill:#536571}</style>',
        '<text x="16" y="27" class="title">The selected trigram score</text>',
        f'<text x="16" y="53" class="strong">Manuscript: {observed}</text>',
        f'<text x="16" y="74">{result["null_ge_observed"]} of 256 shuffled searches reached it</text>',
        '<text x="16" y="104" class="muted">Best score in each complete shuffled search</text>',
    ]
    for index,((_,_,label),count) in enumerate(zip(BINS,bins)):
        y=128+index*36
        width=round(190*count/max(bins))
        parts.extend([
            f'<text x="16" y="{y+13}">{label}</text>',
            f'<rect x="113" y="{y}" width="190" height="17" fill="#edf1f3"/>',
            f'<rect x="113" y="{y}" width="{width}" height="17" fill="#718d9d"/>',
            f'<text x="313" y="{y+13}">{count}</text>',
        ])
    parts.extend(['<text x="16" y="316" class="muted">Same 377 settings searched in every shuffle.</text>','</svg>'])
    return '\n'.join(parts)+'\n'


def main():
    svg=figure()
    if '--check' in sys.argv:
        assert OUT.read_text(encoding='utf-8')==svg
    else:
        OUT.write_text(svg,encoding='utf-8',newline='\n')
    print('PASS: comparison distribution figure')


if __name__=='__main__':main()
