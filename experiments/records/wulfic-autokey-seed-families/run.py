"""Complete pinned source seed grids with whole-procedure shuffle controls."""
import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

from engine import MODES, exhaustive, named, output_hash

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SEED=20261023
NULLS=49
PHASES=('named_keywords','two_rune_seeds','three_rune_seeds','distinct_p21_deor')


def load():
    data=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((HERE/'inputs.json').read_bytes()).hexdigest()==json.loads((HERE/'results.json').read_text(encoding='utf-8'))['input_sha256'] if '--check' in sys.argv else True
    pages={int(k):v for k,v in data['pages'].items()}
    for row in pages.values():
        assert len(row['runes'])>0
        assert hashlib.sha256((ROOT/row['site_path']).read_bytes()).hexdigest()==row['site_sha256']
    return data,pages


def update(total,case,order,detail):
    if case is None:return
    if total['best'] is None or case['ioc']>total['best']['ioc'] or (case['ioc']==total['best']['ioc'] and order<total['best_order']):
        total['best']=case if detail else {'ioc':case['ioc']}
        total['best_order']=order


def fresh():
    return {'configurations':0,'gate_count':0,'hit_count':0,'best':None,'best_order':None}


def full_search(data,pages,ciphers,detail):
    totals={phase:fresh() for phase in PHASES}
    names=list(data['comprehensive_keywords'])
    rows={phase:[] for phase in PHASES} if detail else None
    for source_page in range(21,55):
        row=pages[source_page]
        cipher=np.asarray(ciphers[source_page],dtype=np.int64)
        singletons=row['singletons']
        per={phase:fresh() for phase in PHASES}
        for keyword_index,name in enumerate(names):
            seed=data['comprehensive_keywords'][name]
            for mode in range(6):
                phase='named_keywords';total=totals[phase];local=per[phase]
                total['configurations']+=1;local['configurations']+=1
                ioc,a,b=named(cipher,singletons,seed,mode)
                if ioc is None:continue
                total['gate_count']+=1;local['gate_count']+=1
                hit=ioc>1.3;total['hit_count']+=hit;local['hit_count']+=hit
                case={'page':row['page'],'source_page':source_page,'keyword':name,'seed':seed,
                      'mode':MODES[mode],'ioc':ioc}
                if detail:case['decoded_sha256']=output_hash(a,b,seed)
                order=(source_page,keyword_index,mode)
                update(total,case,order,detail);update(local,case,order,detail)
        for lag,phase in ((2,'two_rune_seeds'),(3,'three_rune_seeds')):
            if lag==3 and len(singletons)<3:continue
            for mode in range(6):
                total=totals[phase];local=per[phase]
                settings=29**lag
                total['configurations']+=settings;local['configurations']+=settings
                outcome,a,b=exhaustive(cipher,singletons,lag,mode)
                total['gate_count']+=outcome['gate_count'];local['gate_count']+=outcome['gate_count']
                total['hit_count']+=outcome['hit_count'];local['hit_count']+=outcome['hit_count']
                if outcome['max_ioc'] is not None:
                    seed=outcome['best_seed']
                    case={'page':row['page'],'source_page':source_page,'seed':seed,
                          'mode':MODES[mode],'ioc':outcome['max_ioc']}
                    if detail:case['decoded_sha256']=output_hash(a,b,seed)
                    order=(source_page,*seed,mode)
                    update(total,case,order,detail);update(local,case,order,detail)
        if source_page<=30:
            phase='distinct_p21_deor';seed=data['p21_distinct_keyword_vectors']['DEOR']
            for mode in range(6):
                total=totals[phase];local=per[phase]
                total['configurations']+=1;local['configurations']+=1
                ioc,a,b=named(cipher,[],seed,mode)
                assert ioc is not None
                total['gate_count']+=1;local['gate_count']+=1
                hit=ioc>1.3;total['hit_count']+=hit;local['hit_count']+=hit
                case={'page':row['page'],'source_page':source_page,'keyword':'DEOR [four rune source array]',
                      'seed':seed,'mode':MODES[mode],'ioc':ioc}
                if detail:case['decoded_sha256']=output_hash(a,b,seed)
                order=(source_page,mode)
                update(total,case,order,detail);update(local,case,order,detail)
        if detail:
            for phase in PHASES:
                local=per[phase];local.pop('best_order')
                rows[phase].append({'page':row['page'],**local})
    for phase in PHASES:
        totals[phase].pop('best_order')
        if detail:totals[phase]['pages']=rows[phase]
    return totals


def execute():
    start=time.monotonic()
    data,pages=load()
    ciphers={old:row['runes'] for old,row in pages.items()}
    observed=full_search(data,pages,ciphers,True)
    rng=random.Random(SEED)
    null=[]
    for trial in range(NULLS):
        shuffled={}
        for old in sorted(pages):
            stream=ciphers[old][:]
            rng.shuffle(stream)
            shuffled[old]=stream
        result=full_search(data,pages,shuffled,False)
        null.append({'trial':trial,'phases':{
            phase:{'max_ioc':None if result[phase]['best'] is None else result[phase]['best']['ioc'],
                   'hit_count':result[phase]['hit_count'],'gate_count':result[phase]['gate_count']}
            for phase in PHASES}})
        if (trial+1)%10==0:print(f'control {trial+1}/{NULLS}',flush=True)
    return {'schema':'liberpedia-wulfic-autokey-seed-results-v1',
            'source_commit':data['source_commit'],
            'input_sha256':hashlib.sha256((HERE/'inputs.json').read_bytes()).hexdigest(),
            'plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),
            'source_duplicate_crosswalk':{'p21_identical_keyword_arrays':17,
                                          'p21_repeated_settings':17*10*6,
                                          'p21_distinct_four_rune_deor_settings':10*6,
                                          'comprehensive_deor_3_rune_repeats_in_phase3':31*6},
            'observed':observed,'null_seed':SEED,'null_trials':NULLS,'null':null,
            'null_ge':{phase:{
                'max_ioc':sum((trial['phases'][phase]['max_ioc'] or -1)>=(observed[phase]['best'] or {'ioc':-1})['ioc'] for trial in null),
                'hit_count':sum(trial['phases'][phase]['hit_count']>=observed[phase]['hit_count'] for trial in null)}
                for phase in PHASES},
            'elapsed_seconds':round(time.monotonic()-start,3)}


def main():
    result=execute();target=HERE/'results.json'
    if '--check' in sys.argv:
        saved=json.loads(target.read_text(encoding='utf-8'))
        result.pop('elapsed_seconds');saved.pop('elapsed_seconds')
        assert result==saved
    else:target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS: all source seed grids and 49 complete-search controls')


if __name__=='__main__':main()
