"""Execute unchanged source sweep_page_seeded with return-preserving observers."""
import hashlib
import json
import time

import numpy as np

import engine as e


def pages(plan):
    from run_stats import load_pages
    result=load_pages()[:-2]
    assert len(result)==55 and max(map(len,result))==277
    for page,indices in zip(plan['page_ids'],result):
        text=(e.ROOT/'text'/f'{page}.txt').read_text(encoding='utf8')
        assert e.source.gp.runes_to_indices(text)==indices
    return result


def main():
    plan=json.loads((e.HERE/'plan.json').read_text(encoding='utf8'))
    for item in plan['inputs']:
        assert e.sha(e.ROOT/item['path'])==item['sha256'],item['path']
    page_values=pages(plan)
    expected=[]
    for assignment in e.assignments():
        for sign in (-1,1):
            for atbash in (0,1):
                expected.append(assignment|{'sign':sign,'atbash':atbash})
    rows=[]
    real_helper=e.source._score_page
    real_beam=e.source.beam
    captured=[]
    def observe_beam(*args):
        value=real_beam(*args)
        captured.append(value)
        return value
    def observe_score(cipher,key,sign,offset,slen,screen_bw,full_bw,length):
        index=len(rows)
        context=expected[index]
        assert sign==context['sign'] and offset==0 and slen==50 and screen_bw==60 and full_bw==300
        assert len(key)==1124 and hashlib.sha256(bytes(map(int,key))).hexdigest()==context['key_sha256']
        transformed=[28-c if context['atbash'] else c for c in page_values[context['source_index']]]
        assert cipher.tolist()==transformed and length==len(transformed)
        captured.clear()
        result=real_helper(cipher,key,sign,offset,slen,screen_bw,full_bw,length)
        screen_score,full_score,translit=result
        assert len(captured)==(2 if screen_score>-6.5 else 1)
        row=context|{'signed_slope':sign*context['slope']%29,
                     'signed_intercept':sign*context['intercept']%29,
                     'screen_indices':captured[0],'screen_score':screen_score,
                     'selected_full':screen_score>-6.5}
        if row['selected_full']:
            full=captured[1]
            row.update(full_indices=full,full_score=full_score,
                       full_sha256=hashlib.sha256(bytes(full)).hexdigest(),source_gate_pass=full_score>-5.5)
            assert (translit is not None)==row['source_gate_pass']
        rows.append(row)
        return result
    started=time.perf_counter()
    try:
        e.source.beam=observe_beam
        e.source._score_page=observe_score
        source_hits,source_best=e.source.sweep_page_seeded([np.array(p,dtype=np.int64) for p in page_values],list(range(55)))
    finally:
        e.source.beam=real_beam
        e.source._score_page=real_helper
    assert len(rows)==660
    assert source_best==max(r['screen_score'] for r in rows)
    expected_hits=[]
    for r in rows:
        if r.get('source_gate_pass',False):
            expected_hits.append((r['full_score'],f"pgseed_{r['mode']}_pg{r['source_index']}",r['sign'],r['atbash'],0,r['source_index'],e.text(r['full_indices'])))
    assert source_hits==expected_hits
    e.write(e.HERE/'cases.json',rows)
    full=[r for r in rows if r['selected_full']]
    result={'schema':'page-number-ramp-target-v1','plan_sha256':e.sha(e.HERE/'plan.json'),
            'target_settings':660,'base_array_assignments':165,'distinct_base_arrays':56,
            'distinct_signed_arrays':112,'full_confirmations':len(full),
            'source_gate_passes':len(source_hits),'original_source_return_values_match':True,
            'best_screen':max(rows,key=lambda r:r['screen_score']),
            'best_full':max(full,key=lambda r:r['full_score']) if full else None,
            'cases_sha256':e.sha(e.HERE/'cases.json'),'elapsed_seconds':time.perf_counter()-started,
            'limit':'Exact assigned source indices, skip rule and two-stage score gates only; score passage is not plaintext validation or a page-number significance test.'}
    e.write(e.HERE/'results.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['best_screen','best_full']},indent=2))


if __name__=='__main__':
    main()
