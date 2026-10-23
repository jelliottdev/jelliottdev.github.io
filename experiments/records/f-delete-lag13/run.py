"""Test a fully specified F deletion followed by a lag-13 two-rune scan."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
LAGS=range(2,29)
TRIALS=499
SEED=13003301


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    alphabet=ROOT/'data/index.json'
    items=json.loads(alphabet.read_text(encoding='utf-8'))['alphabet']
    assert items[0]['latin']=='F'
    lookup={item['rune']:j for j,item in enumerate(items)}
    hashes={'data/index.json':sha(alphabet)}; pages=[]
    for n in range(56):
        path=ROOT/'text'/f'lp2-{n:02d}.txt'
        pages.append([lookup[c] for c in path.read_text(encoding='utf-8') if c in lookup])
        hashes[f'text/lp2-{n:02d}.txt']=sha(path)
    return pages,hashes


def counts(pages):
    out={lag:0 for lag in LAGS}
    opp={lag:0 for lag in LAGS}
    for page in pages:
        n=len(page)
        for lag in LAGS:
            end=max(0,n-lag-1)
            opp[lag]+=end
            out[lag]+=sum(page[k]==page[k+lag] and page[k+1]==page[k+lag+1]
                          for k in range(end))
    return out,opp


def percentile(values,p):
    return sorted(values)[round(p*(len(values)-1))]


def make():
    pages,hashes=load()
    assert sum(map(len,pages))==12956
    kept=[list(filter(lambda x:x!=0,page)) for page in pages]
    assert sum(map(len,kept))==12498
    original,original_opp=counts(pages)
    observed,opportunities=counts(kept)
    rng=random.Random(SEED); null=[]
    for _ in range(TRIALS):
        sample=[]
        for page in kept:
            copy=page.copy();rng.shuffle(copy);sample.append(copy)
        null.append(counts(sample)[0])
    averages={lag:sum(row[lag] for row in null)/TRIALS for lag in LAGS}
    ratios={lag:observed[lag]/averages[lag] for lag in LAGS}
    peaks=[max(row[lag]/averages[lag] for lag in LAGS) for row in null]
    best=max(ratios.values())
    lag13=[row[13] for row in null]
    return {'schema':'liberpedia-f-delete-lag13-v1','input_sha256':hashes,
            'rule':'Delete every F (index 0) within each page; join neighboring non-F runes; count exact two-rune recurrences at lag 13, then scan lags 2–28.',
            'pages':56,'original_runes':12956,'deleted_f':458,'remaining_runes':12498,
            'lag13':{'original_count':original[13],'original_opportunities':original_opp[13],
                     'after_deletion_count':observed[13],'after_deletion_opportunities':opportunities[13],
                     'null_mean':round(averages[13],3),
                     'null_middle_95':[percentile(lag13,.025),percentile(lag13,.975)],
                     'null_at_least_observed':sum(x>=observed[13] for x in lag13)},
            'lag_scan':{'lags':[2,28], 'observed_counts':{str(k):v for k,v in observed.items()},
                        'null_means':{str(k):round(v,5) for k,v in averages.items()},
                        'best_ratio':round(best,6),'best_lags':[lag for lag in LAGS if ratios[lag]==best],
                        'null_best_ratio_middle_95':[round(percentile(peaks,.025),6),round(percentile(peaks,.975),6)],
                        'null_best_at_least_observed':sum(x>=best for x in peaks)},
            'reference':{'trials':TRIALS,'seed':SEED,
                         'unit':'Shuffle retained non-F runes separately inside each page; repeat deletion-stage scan and same lag search.'}}


def svg(r):
    raw=r['lag13']['original_count']; observed=r['lag13']['after_deletion_count'];
    lo,hi=r['lag13']['null_middle_95']; mean=r['lag13']['null_mean']
    top=max(raw,observed,hi)+5
    x=lambda n:28+round(n/top*290,1)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="390" height="245" viewBox="0 0 390 245" role="img" aria-labelledby="t d">\n'
            '<title id="t">Lag-13 two-rune matches after deleting F</title>\n'
            '<desc id="d">Observed lag-13 count after F deletion compared with a within-page shuffle reference.</desc>\n'
            '<rect width="390" height="245" fill="#f5f6f7"/>\n'
            '<g font-family="Arial,sans-serif" fill="#263740">\n'
            '<text x="20" y="29" font-size="18" font-weight="bold">Does F deletion reveal lag 13?</text>\n'
            '<text x="20" y="51" font-size="12">Exact matching two-rune blocks · LP2-00–55</text>\n'
            '<text x="20" y="79" font-size="13">Original stream</text>\n'
            f'<rect x="28" y="86" width="{x(raw)-28}" height="17" fill="#87939c"/>\n'
            f'<text x="{min(338,x(raw)+7)}" y="100" font-size="13">{raw}</text>\n'
            '<text x="20" y="133" font-size="13">After deleting F</text>\n'
            f'<rect x="28" y="140" width="{x(observed)-28}" height="17" fill="#315f78"/>\n'
            f'<text x="{min(338,x(observed)+7)}" y="154" font-size="13">{observed}</text>\n'
            '<text x="20" y="187" font-size="13">Page-shuffle reference</text>\n'
            f'<rect x="{x(lo)}" y="194" width="{x(hi)-x(lo)}" height="17" fill="#a0adb4"/>\n'
            f'<line x1="{x(mean)}" x2="{x(mean)}" y1="190" y2="215" stroke="#263740" stroke-width="2"/>\n'
            f'<text x="20" y="233" font-size="12">Middle 95%: {lo}–{hi}; line: mean {mean:g}</text>\n'
            '</g></svg>\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    r=make();image=svg(r);path=HERE/'results.json';figure=HERE/'comparison.svg'
    if args.check:
        assert json.loads(path.read_text(encoding='utf-8'))==r
        assert figure.read_text(encoding='utf-8')==image
        print('PASS F-deletion lag-13 scan')
    else:
        path.write_bytes((json.dumps(r,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
        figure.write_bytes(image.encode('utf-8'))
        print(json.dumps({'lag13':r['lag13'],'lag_scan':{k:v for k,v in r['lag_scan'].items() if k not in ('observed_counts','null_means')}},indent=2))

if __name__=='__main__':main()
