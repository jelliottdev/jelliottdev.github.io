"""Independent trace and beam replay; never imports the benchmark implementation."""
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/plans/decoder-skip-controls.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def keys(seed,repeat,slots):
    prefix=('liberpedia-decoder-control:'+str(seed)).encode('ascii')
    stream=b''.join(hashlib.sha256(prefix+i.to_bytes(4,'big')).digest() for i in range((slots+31)//32))
    return [b%29 for b in stream for _ in range(repeat)][:slots]


def audit_trace(plant,key):
    p=plant['plaintext'];c=plant['ciphertext'];trace=plant['encoder_trace'];mode=plant['encoder']
    assert len(p)==len(c)==len(trace)
    rng=random.Random(3301+plant['seed']);pointer=0
    for i,t in enumerate(trace):
        start=pointer;drift=[]
        if mode=='drift-skip' and i==len(p)//2:
            drift=[pointer];pointer+=1
        decisions=[];rejections=[];rewrite=False
        accepted=t['accepted_slot']
        assert type(accepted) is int and pointer<=accepted<len(key)
        for slot in range(pointer,accepted+1):
            proposed=(p[i]+key[slot])%29
            suppress=False
            if i and proposed==c[i-1] and mode!='rigid':
                draw=rng.randrange(100);decisions.append({'key_slot':slot,'draw':draw});suppress=draw<83
            if slot<accepted:
                assert mode in ('skip','drift-skip') and suppress
                rejections.append(slot)
            else:
                assert not (mode in ('skip','drift-skip') and suppress)
                rewrite=mode=='rewrite' and suppress
        expected={'position':i,'plain':p[i],'pointer_before':start,'unrelated_slots':drift,
                  'rejected_slots':rejections,'decisions':decisions,'accepted_slot':accepted,
                  'proposed':proposed,'rewritten':rewrite,'cipher':(proposed+rewrite)%29}
        assert t==expected and c[i]==expected['cipher']
        assert (c[i]-rewrite-key[accepted])%29==p[i]
        pointer=accepted+1


def replay(cipher,key,width,limit,labels,weights,floor,truth,trace):
    # Store states as (key path, rune path, rendered prefix, cumulative score).
    states=[((),(),'',0.0)];invalid=None;pruned=None
    truth_slots=tuple(t['accepted_slot'] for t in trace)
    for i,c in enumerate(cipher):
        actual=truth_slots[i];previous=truth_slots[i-1] if i else -1
        legal=(actual==0) if i==0 else (1<=actual-previous<=limit+1 and
              all(key[k]==(cipher[i-1]-truth[i])%29 for k in range(previous+1,actual)))
        legal=legal and (c-key[actual])%29==truth[i]
        if invalid is None and not legal:invalid=i
        expanded=[]
        for slots,indices,text,total in states:
            first=slots[-1]+1 if slots else 0
            stop=min(len(key),first+limit+1) if slots else 1
            for accepted in range(first,stop):
                p=(c-key[accepted])%29
                if i and any(key[k]!=(cipher[i-1]-p)%29 for k in range(first,accepted)):continue
                rendered=text+labels[p];value=total
                for end in range(max(4,len(text)+1),len(rendered)+1):
                    value+=weights.get(rendered[end-4:end],floor)
                expanded.append((slots+(accepted,),indices+(p,),rendered,value))
        assert expanded
        expanded.sort(key=lambda v:(-v[3],v[0],v[1]))
        states=expanded[:width]
        if pruned is None and invalid is None:
            if not any(s==truth_slots[:i+1] and p==tuple(truth[:i+1]) for s,p,_,_ in states):pruned=i
    slots,indices,text,total=states[0]
    return slots,indices,text,total,invalid,pruned


def check(report_path):
    plan=json.loads(PLAN.read_bytes());report=json.loads(report_path.read_bytes())
    assert report['plan_sha256']==sha(PLAN)
    assert report['implementation_sha256']==sha(ROOT/'scripts/decoder_skip_controls.py')
    assert report['producer_sha256']==sha(ROOT/'scripts/run_decoder_skip_controls.py')
    for source in plan['inputs']:assert sha(ROOT/source['path'])==source['sha256'],source['path']
    counts={}
    for line in (ROOT/'experiments/records/english-scorer-controls/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        word,count=line.split();assert word not in counts;counts[word]=int(count)
    denominator=sum(counts.values());base=math.log10(denominator)
    weights={g:math.log10(n)-base for g,n in counts.items()};floor=math.log10(.01)-base
    expected_grid=list(itertools.product(plan['sections'],plan['seeds'],plan['key_repetitions'],plan['encoders']))
    assert len(report['plants'])==len(expected_grid)==216
    rows_checked=0
    for plant,(section,seed,repeat,encoder) in zip(report['plants'],expected_grid,strict=True):
        assert (plant['section'],plant['seed'],plant['key_repetition'],plant['encoder'])==(section,seed,repeat,encoder)
        with (ROOT/f'exports/readings/{section}.csv').open(encoding='utf-8',newline='') as f:source=list(csv.DictReader(f))
        selected=source[:plan['prefix_runes']];truth=[int(r['output_index']) for r in selected]
        assert plant['plaintext']==truth and plant['source_rows_available']==len(source)
        assert plant['endpoints']=={k:[selected[0][k],selected[-1][k]] for k in ['page','page_rune_ordinal','section_rune_ordinal']}
        correct=keys(seed,repeat,plan['key_slots']);audit_trace(plant,correct)
        configs=[(condition,decoder,width,limit) for condition in ['correct','wrong']
                 for decoder,width,limit in [('rigid',None,0)]+[('beam',w,s) for w in plan['beam_widths'] for s in plan['maximum_skips']]]
        assert len(plant['results'])==len(configs)
        for result,(condition,decoder,width,limit) in zip(plant['results'],configs,strict=True):
            assert (result['key_condition'],result['decoder'],result['width'],result['maximum_skip'])==(condition,decoder,width,limit)
            key=correct if condition=='correct' else keys(seed+1000,repeat,plan['key_slots'])
            slots,indices,text,total,invalid,pruned=replay(plant['ciphertext'],key,width or 1,limit,plan['latin'],weights,floor,truth,plant['encoder_trace'])
            assert result['slots']==list(slots) and result['indices']==list(indices) and result['transliteration']==text
            assert result['first_invalid_truth_step']==invalid
            assert result['first_pruned_truth_step']==(pruned if decoder=='beam' else None)
            # Independent full-text score using count/total, rather than incremental deltas.
            score=math.fsum(math.log10(counts.get(text[i:i+4],.01)/denominator) for i in range(len(text)-3))
            assert math.isclose(result['cumulative_score'],score,rel_tol=0,abs_tol=1e-8)
            assert math.isclose(total,score,rel_tol=0,abs_tol=1e-8)
            normalized=score/(len(text)-3) if len(text)>3 else None
            if normalized is None:assert result['normalized_score'] is None
            else:assert math.isclose(result['normalized_score'],normalized,rel_tol=0,abs_tol=1e-10)
            matches=[a==b for a,b in zip(indices,truth,strict=True)]
            assert result['exact_match']==all(matches) and result['matching_indices']==sum(matches)
            assert result['length']==len(truth)
            assert result['longest_correct_prefix']==next((i for i,m in enumerate(matches) if not m),len(matches))
            assert result['score_accepted']==(normalized is not None and normalized>=plan['threshold'])
            rows_checked+=1
        if encoder==plan['encoders'][-1] and seed==plan['seeds'][-1] and repeat==plan['key_repetitions'][-1]:
            print('Independently checked',section,flush=True)
    assert rows_checked==2160
    return {'status':'independent trace, candidate and beam replay passed; human review pending',
            'plants_checked':216,'decoder_results_checked':rows_checked,'report_sha256':sha(report_path),
            'checker_sha256':sha(Path(__file__))}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('report',type=Path);parser.add_argument('--receipt',type=Path,required=True);args=parser.parse_args()
    if args.receipt.exists():parser.error('Choose a new receipt path')
    receipt=check(args.report)
    with args.receipt.open('x',encoding='utf-8',newline='\n') as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps(receipt))
