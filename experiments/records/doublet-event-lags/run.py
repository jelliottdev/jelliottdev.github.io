"""Recount event lags 1--3; descriptive only, with no fitted parameters."""
import argparse
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from rune_doublets import report as extract

def report():
    source = extract()
    lookup = {a['rune']: i for i, a in enumerate(source['alphabet'])}
    events = [dict(page=e['left']['page'], rune_index=e['left']['rune_index_zero_based'], value=lookup[e['left']['rune']]) for e in source['page']['occurrences']]
    n = len(events)
    # Ordered distinct event positions: exact expectation under a uniform shuffle.
    null = Counter((b['value']-a['value']) % 29 for i,a in enumerate(events) for j,b in enumerate(events) if i != j)
    rows = []
    for lag in (1,2,3):
        pairs = [dict(left=i,right=i+lag,directed=(events[i+lag]['value']-events[i]['value']) % 29,crosses_page=events[i]['page'] != events[i+lag]['page']) for i in range(n-lag)]
        histogram = Counter(p['directed'] for p in pairs)
        circular = [min(p['directed'],29-p['directed']) for p in pairs]
        rows.append(dict(lag=lag,pair_count=len(pairs),cross_page_count=sum(p['crosses_page'] for p in pairs),directed_histogram=[histogram[k] for k in range(29)],circular_sum=sum(circular),circular_mean=str(Fraction(sum(circular),len(pairs))),plus4_count=histogram[4],plus4_rate=str(Fraction(histogram[4],len(pairs))),distance_5_12_14_count=sum(d in (5,12,14) for d in circular),pairs=pairs))
    return dict(input_sha256=source['input_sha256'],events=events,lags=rows,shuffle_plus4_probability=str(Fraction(null[4],n*(n-1))),shuffle_directed_probabilities=[str(Fraction(null[k],n*(n-1))) for k in range(29)],scope='Overlapping within-page doublets, LP2-00--55, headings included; event comparisons cross pages; forward difference modulo 29; no end wrap; no significance test.')

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=report()
    if args.check:
        assert result == json.loads(Path(__file__).with_name('results.json').read_text())
        print('PASS: all event-lag pairs, histograms and expectations reproduced')
    else:
        print(json.dumps(result,indent=2))
