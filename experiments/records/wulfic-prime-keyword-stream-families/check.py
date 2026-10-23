"""Independent scalar check of saved winners, inputs, controls and selection counts."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from engine import STEPPED_VARIANTS, key_matrix, prime_key, prime_orderings

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def scalar_decode(cipher, key, mode, skip=False):
    out=[]
    index=0
    for position,value in enumerate(cipher):
        kval=int(key[index if skip else position % len(key)])
        if mode=='sub': plain=(value-kval)%29
        elif mode=='add': plain=(value+kval)%29
        else: plain=(kval-value)%29
        out.append(plain)
        if skip and not (value==0 and plain==0):index+=1
    return out


def scalar_ioc(values):
    n=len(values)
    frequencies=Counter(values)
    return 29*sum(count*(count-1) for count in frequencies.values())/(n*(n-1))


def verify_case(case, branch, inputs, matrix, names):
    page=next(row for row in inputs['pages'].values() if row['site_page']==case['page'])
    cipher=page['runes']
    if branch=='keyword_only':key=inputs['keyword_only'][case['keyword']]
    elif branch=='prime_stream':
        sequences, all_primes=prime_orderings(len(cipher))
        prime_values=dict(sequences)[case['sequence']]
        key=prime_key(prime_values,case['key_form'],all_primes).tolist()
    else:
        wi=names.index(case['keyword'])
        vi=STEPPED_VARIANTS.index(case['variant'])
        index=(wi*8+vi)*1001+case['offset']
        key=matrix[index,:len(cipher)].tolist()
    plain=scalar_decode(cipher,key,case['mode'],case.get('f_skip',False))
    assert hashlib.sha256(bytes(plain)).hexdigest()==case['decoded_sha256'], (branch,case)
    assert abs(scalar_ioc(plain)-case['ioc'])<1e-12
    if branch=='keyword_only':singleton_positions=page['keyword_singletons']
    elif branch=='prime_stream':singleton_positions=[] if case['f_skip'] else page['prime_singletons']
    else:singleton_positions=page['stepped_singletons']
    if branch!='keyword_stepped':
        assert sum(plain[pos] in (10,24) for pos in singleton_positions)==case['singletons_fit']
        assert len(singleton_positions)==case['singletons_total']
    else:assert all(plain[pos] in (10,24) for pos in singleton_positions)


def main():
    inputs=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    results=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((HERE/'inputs.json').read_bytes()).hexdigest()==results['input_sha256']
    assert len(results['null'])==49 and [x['trial'] for x in results['null']]==list(range(49))
    assert all(len(x['runes'])>0 for x in inputs['pages'].values())
    for row in inputs['pages'].values():
        assert hashlib.sha256((ROOT/row['site_path']).read_bytes()).hexdigest()==row['site_sha256']
    names,matrix,max_index=key_matrix(inputs['stepped_keywords'],max(len(x['runes']) for x in inputs['pages'].values()))
    assert matrix.shape[0]==results['stepped_key_matrix']['rows']==160160
    assert max_index==results['stepped_key_matrix']['max_prime_index_used']
    observed=results['observed']
    assert observed['keyword_only']['candidate_count']==540
    assert observed['prime_stream']['candidate_count']==11880
    assert observed['keyword_stepped']['source_configurations']==5285280
    for branch,record in observed.items():
        selected=[]
        if branch=='keyword_only': selected=[record['max_ioc'],*([record['best_all_singleton_fit']] if record['best_all_singleton_fit'] else [])]
        elif branch=='prime_stream': selected=[record['max_ioc'],record['source_top_retained']]
        else:selected=[record['max_ioc_after_singleton_gate']]
        for page_row in record['pages']:
            selected.append(page_row.get('max_ioc') or page_row.get('max_ioc_after_singleton_gate'))
        for case in selected:
            if case:verify_case(case,branch,inputs,matrix,names)
    null=results['null']
    expected={
        'keyword_only_max_ioc':sum(x['keyword_only_max_ioc']>=observed['keyword_only']['max_ioc']['ioc'] for x in null),
        'prime_stream_max_ioc':sum(x['prime_stream_max_ioc']>=observed['prime_stream']['max_ioc']['ioc'] for x in null),
        'keyword_stepped_max_ioc':sum((x['keyword_stepped_max_ioc'] or -1)>=observed['keyword_stepped']['max_ioc_after_singleton_gate']['ioc'] for x in null),
        'keyword_stepped_hit_count':sum(x['keyword_stepped_ioc_above_1_3_count']>=observed['keyword_stepped']['ioc_above_1_3_count'] for x in null),
    }
    assert expected==results['null_ge']
    for control in results['planted_controls']:
        assert control['exact_recovery'] and control['normalized_ioc']>1.3
    print('PASS: independent scalar outputs, source counts, 49 controls and input hashes')


if __name__=='__main__':main()
