"""Full direct LP2 page-pair arithmetic and conditional shuffle census."""
import argparse
import hashlib
import json
import random
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ALPHABET='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
INDEX={ch:i for i,ch in enumerate(ALPHABET)}
Q=29
TRIALS=256
SEED=330129


def pages():
    out=[]
    for number in range(56):
        page_id=f'lp2-{number:02d}'
        raw=(ROOT/'text'/f'{page_id}.txt').read_text(encoding='utf-8')
        values=[INDEX[ch] for ch in raw if ch in INDEX]
        if values:
            out.append((page_id,values))
    assert len(out)==55
    return out


def band_limits(page_lengths):
    lengths=sorted(set(page_lengths))
    return [tuple([0]+[length for length in lengths if length<=n]) for n in page_lengths]


def shuffle_pages(values,limits,rng):
    out=[]
    moved=0
    for stream,edges in zip(values,limits):
        new=list(stream)
        for start,end in zip(edges,edges[1:]):
            band=new[start:end]
            rng.shuffle(band)
            new[start:end]=band
        moved+=sum(a!=b for a,b in zip(stream,new))
        out.append(new)
    return out,moved


def ioc_numerator_counts(a,b):
    n=min(len(a),len(b))
    plus=[0]*Q
    minus=[0]*Q
    for j in range(n):
        x,y=a[j],b[j]
        plus[(x+y)%Q]+=1
        minus[(x-y)%Q]+=1
    denominator=n*(n-1)
    return (sum(v*(v-1) for v in plus)/denominator,
            sum(v*(v-1) for v in minus)/denominator,n)


def grid(ids,streams,store_cases=False):
    top={'ioc':-1.0}
    cases=[] if store_cases else None
    for i in range(len(streams)):
        for j in range(i+1,len(streams)):
            positive,negative,n=ioc_numerator_counts(streams[i],streams[j])
            for operation,value in (('sum',positive),('difference',negative)):
                if value>top['ioc']:
                    top={'page_a':ids[i],'page_b':ids[j],
                         'operation':operation,'compared_runes':n,'ioc':value}
                if store_cases:
                    cases.append({'page_a':ids[i],'page_b':ids[j],
                                  'operation':operation,'compared_runes':n,'ioc':value})
    return top,cases


def make_results():
    archive=pages()
    ids=[p[0] for p in archive]
    streams=[p[1] for p in archive]
    lengths=[len(p) for p in streams]
    edges=band_limits(lengths)
    band_sizes=[b-a for e in edges for a,b in zip(e,e[1:])]
    observed,cases=grid(ids,streams,True)
    assert len(cases)==2970
    # A shifted copy is a positive control for the pairwise difference rule.
    planted=list(range(29))*3
    shifted=[(v+7)%Q for v in planted]
    planted_sum,planted_difference,_=ioc_numerator_counts(planted,shifted)
    assert planted_difference==1.0 and planted_sum<1.0
    rng=random.Random(SEED)
    null_max=[]
    moved_total=0
    for _ in range(TRIALS):
        shuffled,moved=shuffle_pages(streams,edges,rng)
        moved_total+=moved
        top,_=grid(ids,shuffled)
        null_max.append(top['ioc'])
    exceed=sum(value>=observed['ioc'] for value in null_max)
    null_sorted=sorted(null_max)
    result={'schema':'liberpedia-lp2-page-pair-alignment-results-v1',
            'plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),
            'page_count':len(ids),'page_lengths':dict(zip(ids,lengths)),
            'pair_count':len(streams)*(len(streams)-1)//2,'operation_count':len(cases),
            'band_profile':{'distinct_page_lengths':len(set(lengths)),'total_bands':len(band_sizes),
                            'singleton_bands':sum(n==1 for n in band_sizes),
                            'min_band_size':min(band_sizes),'max_band_size':max(band_sizes),
                            'moved_fraction_across_all_trials':moved_total/(TRIALS*sum(lengths))},
            'observed_max':observed,'null_trials':TRIALS,'null_seed':SEED,
            'null_maxima':null_max,'null_max_median':(null_sorted[127]+null_sorted[128])/2,
            'null_max_95th':null_sorted[int(.95*TRIALS)-1],
            'null_exceedances':exceed,'empirical_global_p':(1+exceed)/(1+TRIALS),
            'planted_shifted_copy':{'difference_ioc':planted_difference,'sum_ioc':planted_sum},
            'cases':cases}
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=make_results()
    if args.check:
        assert result==json.loads((HERE/'results.json').read_text(encoding='utf-8'))
        print('PASS: full page-pair and conditional-shuffle census matches stored results')
    else:
        (HERE/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps({k:result[k] for k in ('observed_max','null_max_median','null_max_95th','null_exceedances','empirical_global_p','band_profile')},indent=2))
