"""Independent page-JSON census and global-max conditional-shuffle replay."""
import json
import random
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ALPHABET='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
VALUE={ch:i for i,ch in enumerate(ALPHABET)}


def source_pages():
    out=[]
    for number in range(56):
        id=f'lp2-{number:02d}'
        page=json.loads((ROOT/'data/pages'/f'{id}.json').read_text(encoding='utf-8'))
        text=''.join(line['raw'] for line in page['lines'])
        values=[VALUE[ch] for ch in text if ch in VALUE]
        if values:
            out.append((id,values))
    assert len(out)==55
    return out


def score(a,b,sign):
    length=min(len(a),len(b))
    histogram=Counter((a[k]+sign*b[k])%29 for k in range(length))
    return sum(v*(v-1) for v in histogram.values())/(length*(length-1))


def all_scores(pages):
    cases=[]
    for i,(name_a,a) in enumerate(pages):
        for name_b,b in pages[i+1:]:
            for op,sign in (('sum',1),('difference',-1)):
                cases.append((name_a,name_b,op,min(len(a),len(b)),score(a,b,sign)))
    assert len(cases)==2970
    return cases


def shuffled_pages(pages,rng):
    lengths=sorted({len(v) for _,v in pages})
    out=[]
    moved=0
    profiles=[]
    for name,original in pages:
        after=original[:]
        edges=[0]+[bound for bound in lengths if bound<=len(original)]
        for start,stop in zip(edges,edges[1:]):
            part=after[start:stop]
            rng.shuffle(part)
            after[start:stop]=part
            assert Counter(part)==Counter(original[start:stop])
            profiles.append(stop-start)
        moved+=sum(x!=y for x,y in zip(original,after))
        out.append((name,after))
    return out,moved,profiles


def main():
    result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    pages=source_pages()
    planted=list(range(29))*3
    shifted=[(value+7)%29 for value in planted]
    assert score(planted,shifted,-1)==1.0
    assert score(planted,shifted,1)<1.0
    assert result['planted_shifted_copy']=={
        'difference_ioc':score(planted,shifted,-1),
        'sum_ioc':score(planted,shifted,1)}
    observed=all_scores(pages)
    stored=[(v['page_a'],v['page_b'],v['operation'],v['compared_runes'],v['ioc']) for v in result['cases']]
    assert observed==stored
    top=max(observed,key=lambda v:v[4])
    assert top==(result['observed_max']['page_a'],result['observed_max']['page_b'],
                 result['observed_max']['operation'],result['observed_max']['compared_runes'],
                 result['observed_max']['ioc'])
    rng=random.Random(330129)
    maxima=[]
    total_moved=0
    first_profile=None
    for _ in range(256):
        trial,moved,profile=shuffled_pages(pages,rng)
        total_moved+=moved
        if first_profile is None:
            first_profile=profile
        else:
            assert first_profile==profile
        maxima.append(max(v[4] for v in all_scores(trial)))
    assert maxima==result['null_maxima']
    assert sum(n==1 for n in first_profile)==result['band_profile']['singleton_bands']
    assert len(first_profile)==result['band_profile']['total_bands']
    assert total_moved/(256*sum(len(v) for _,v in pages))==result['band_profile']['moved_fraction_across_all_trials']
    exceed=sum(value>=top[4] for value in maxima)
    assert exceed==result['null_exceedances']
    assert (1+exceed)/257==result['empirical_global_p']
    # Reversing the ordered pair only negates difference symbols; IoC is unchanged.
    for _,a in pages[:3]:
        for _,b in pages[-3:]:
            assert score(a,b,-1)==score(b,a,-1)
    print(f"PASS: 2,970 observed streams, 256 shared-shuffle global maxima, p={result['empirical_global_p']:.4f}")


if __name__=='__main__':
    main()
