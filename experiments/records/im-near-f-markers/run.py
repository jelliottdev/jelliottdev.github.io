"""Test a fixed, local reading of proposed I/M markers around F runes."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
TRIALS=999
SEED=33014055
F,I,M=0,10,19
RADIUS=2


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    alphabet=ROOT/'data/index.json'
    symbols=json.loads(alphabet.read_text(encoding='utf-8'))['alphabet']
    assert [symbols[k]['latin'] for k in (F,I,M)]==['F','I','M']
    lookup={x['rune']:n for n,x in enumerate(symbols)}
    sources={'data/index.json':sha(alphabet)}; pages=[]
    for n in range(56):
        path=ROOT/'text'/f'lp2-{n:02d}.txt'
        pages.append([lookup[c] for c in path.read_text(encoding='utf-8') if c in lookup])
        sources[f'text/lp2-{n:02d}.txt']=sha(path)
    return pages,sources


def measure(pages):
    exposed=0; f_count=0; by_page=[]
    for n,page in enumerate(pages):
        count=0; marked=0
        for k,symbol in enumerate(page):
            if symbol!=F: continue
            count+=1
            low=max(0,k-RADIUS); high=min(len(page),k+RADIUS+1)
            if any(page[j] in (I,M) for j in range(low,high) if j!=k): marked+=1
        if count: by_page.append({'page':f'lp2-{n:02d}','f':count,'near_i_or_m':marked})
        exposed+=marked; f_count+=count
    return {'f_runes':f_count,'near_i_or_m':exposed,'fraction':round(exposed/f_count,6),
            'by_page':by_page}


def percentile(values,p):
    ordered=sorted(values)
    return ordered[round(p*(len(ordered)-1))]


def make():
    pages,sources=load(); seen=measure(pages)
    assert sum(map(len,pages))==12956 and seen['f_runes']==458
    rng=random.Random(SEED); null=[]
    for _ in range(TRIALS):
        shuffled=[]
        for page in pages:
            copy=page.copy(); rng.shuffle(copy); shuffled.append(copy)
        null.append(measure(shuffled)['near_i_or_m'])
    return {'schema':'liberpedia-im-near-f-markers-v1','input_sha256':sources,
            'rule':'Within a page, an F is exposed when an I or M rune is 1–2 rune positions before or after it; no words or punctuation counted.',
            'observed':seen,'reference':{'trials':TRIALS,'seed':SEED,'shuffle_unit':'runes within each page; preserves per-page counts and length',
            'middle_95':[percentile(null,.025),percentile(null,.975)],
            'mean':round(sum(null)/TRIALS,3),
            'at_least_observed':sum(x>=seen['near_i_or_m'] for x in null),
            'at_most_observed':sum(x<=seen['near_i_or_m'] for x in null),
            'counts':null}}


def svg(r):
    o=r['observed']['near_i_or_m']; ref=r['reference']; a,b=ref['middle_95']; mean=ref['mean']
    maxv=max(o,b,mean)+12
    x=lambda v:25+round(v/maxv*280,1)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="390" height="215" viewBox="0 0 390 215" role="img" aria-labelledby="t d">\n'
            '<title id="t">I or M within two runes of F</title>\n'
            '<desc id="d">Observed count compared with page-preserving shuffled range.</desc>\n'
            '<rect width="390" height="215" fill="#f5f6f7"/>\n'
            '<g font-family="Arial,sans-serif" fill="#263740">\n'
            '<text x="20" y="29" font-size="18" font-weight="bold">Are I/M close to F?</text>\n'
            '<text x="20" y="52" font-size="12">Within two rune positions · LP2-00–55</text>\n'
            '<text x="20" y="85" font-size="13">Actual pages</text>\n'
            f'<rect x="25" y="94" width="{x(o)-25}" height="18" fill="#315f78"/>\n'
            f'<text x="{min(327,x(o)+6)}" y="109" font-size="13">{o}</text>\n'
            '<text x="20" y="145" font-size="13">Page shuffles</text>\n'
            f'<rect x="{x(a)}" y="153" width="{x(b)-x(a)}" height="18" fill="#8a9ba4"/>\n'
            f'<line x1="{x(mean)}" x2="{x(mean)}" y1="149" y2="177" stroke="#263740" stroke-width="2"/>\n'
            f'<text x="20" y="199" font-size="12">Middle 95%: {a}–{b}; line: mean {mean:g}</text>\n'
            '</g></svg>\n')


def main():
    p=argparse.ArgumentParser(); p.add_argument('--check',action='store_true'); args=p.parse_args()
    r=make(); picture=svg(r); path=HERE/'results.json'; visual=HERE/'proximity.svg'
    if args.check:
        assert json.loads(path.read_text(encoding='utf-8'))==r
        assert visual.read_text(encoding='utf-8')==picture
        print('PASS I/M near F markers')
    else:
        path.write_bytes((json.dumps(r,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
        visual.write_bytes(picture.encode('utf-8'))
        print(json.dumps({'observed':r['observed']['near_i_or_m'],'f':r['observed']['f_runes'],
                          'reference':{k:v for k,v in r['reference'].items() if k!='counts'}},indent=2))

if __name__=='__main__': main()
