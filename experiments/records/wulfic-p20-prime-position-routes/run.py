"""Run the exact P20 route cohort and a separate whole-selection control."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path

import numpy as np

from engine import source_stage
from gate import git_bytes, staged_source

HERE=Path(__file__).resolve().parent
SEED=20261023
NULLS=199


def compact(stage:dict, full:bool)->dict:
    rows=[]
    for route in stage['routes']:
        row={k:route[k] for k in ('name','trigrams','source_gate','reported','ioc','complete_permutation')}
        if full:
            row['length']=len(route['values'])
            row['decode_sha256']=hashlib.sha256(bytes(route['values'])).hexdigest()
            row['first_40_values']=route['values'][:40]
        rows.append(row)
    return {'prime_position_count':stage['prime_position_count'],
            'nonprime_position_count':stage['nonprime_position_count'],
            'prime_index_value_count':stage['prime_index_value_count'],
            'nonprime_index_value_count':stage['nonprime_index_value_count'],
            'best_shift':stage['best_shift'],'nonprime_ioc':stage['nonprime_ioc'],
            'prime_value_ioc':stage['prime_value_ioc'],
            'nonprime_value_ioc':stage['nonprime_value_ioc'],
            'route_count':len(rows),
            'source_reported_count':sum(r['reported'] for r in rows),
            'max_trigrams':max(r['trigrams'] for r in rows),
            'max_route_names':[r['name'] for r in rows if r['trigrams']==max(t['trigrams'] for t in rows)],
            'routes':rows if full else None}


def build(source_root:Path|None)->tuple[dict,dict|None]:
    plan_raw=(HERE/'plan.json').read_bytes()
    input_raw=(HERE/'inputs.json').read_bytes()
    gate_raw=(HERE/'gate.json').read_bytes()
    inputs=json.loads(input_raw)
    assert inputs['page']=='lp2-03' and len(inputs['values'])==217
    assert json.loads(gate_raw)['synthetic_planted_170_rune_column_recovery']
    observed=source_stage(inputs['values'],inputs['deor_key_prefix'])
    assert len(observed['routes'])==58
    assert observed['best_shift']==0
    source_receipt=None
    if source_root is not None:
        raw=git_bytes(source_root,'pages/page_20/runes.txt')
        assert hashlib.sha256(raw).hexdigest()==inputs['source_page_sha256']
        poem=git_bytes(source_root,'data/corpora/deor_poem.txt')
        assert hashlib.sha256(poem).hexdigest()==inputs['source_deor_sha256']
        source,printed=staged_source(source_root,raw)
        assert source['total']==217 and source['best_shift']==observed['best_shift']
        assert source['np_plain']==[inputs['values'][i] for i in range(217) if not source['is_prime'](i)]
        ours={r['name']:r for r in observed['routes'] if r['reported']}
        actual={name:(ioc,info) for name,ioc,info in source['results']}
        assert set(ours)==set(actual)
        for name,route in ours.items():
            assert abs(route['ioc']-actual[name][0])<1e-12
        source_receipt={'schema':'wulfic-p20-original-source-receipt-v1',
                        'original_unmodified_script':True,
                        'source_stdout_sha256':hashlib.sha256(printed.encode('utf8')).hexdigest(),
                        'source_reported_count':len(actual),
                        'source_reported_route_names':list(actual),
                        'source_best_shift':source['best_shift'],
                        'source_rune_count':source['total']}
    rng=np.random.default_rng(SEED)
    nulls=[]
    for rep in range(NULLS):
        shuffled=rng.permutation(np.asarray(inputs['values'],dtype=np.int16)).tolist()
        stage=source_stage(shuffled,inputs['deor_key_prefix'])
        item=compact(stage,False)
        nulls.append({'replicate':rep,'max_trigrams':item['max_trigrams'],
                      'source_reported_count':item['source_reported_count']})
    obs=compact(observed,True)
    result={'schema':'wulfic-p20-prime-position-results-v1',
            'plan_sha256':hashlib.sha256(plan_raw).hexdigest(),
            'inputs_sha256':hashlib.sha256(input_raw).hexdigest(),
            'gate_sha256':hashlib.sha256(gate_raw).hexdigest(),
            'source_page':'pages/page_20/runes.txt','actual_page':'lp2-03',
            'observed':obs,
            'controls':{'seed':SEED,'replicates':NULLS,'rows':nulls,
                        'max_trigram_median':statistics.median(x['max_trigrams'] for x in nulls),
                        'max_trigram_exceedances':sum(x['max_trigrams']>=obs['max_trigrams'] for x in nulls),
                        'reported_count_median':statistics.median(x['source_reported_count'] for x in nulls),
                        'reported_count_exceedances':sum(x['source_reported_count']>=obs['source_reported_count'] for x in nulls)}}
    return result,source_receipt


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-root',type=Path)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result,source_receipt=build(args.source_root)
    for filename,data in [('results.json',result),('source-run.json',source_receipt)]:
        if data is None:
            continue
        raw=json.dumps(data,ensure_ascii=False,indent=2).encode('utf8')+b'\n'
        target=HERE/filename
        if args.check:
            assert target.read_bytes()==raw
        else:
            target.write_bytes(raw)
    print(f"{result['observed']['route_count']} routes, {result['observed']['source_reported_count']} source-reported; max {result['observed']['max_trigrams']} trigrams; {result['controls']['max_trigram_exceedances']}/{NULLS} full shuffles reach it.")


if __name__=='__main__':
    main()
