"""Independent plant inversions, source full-control parity and failure diagnosis."""
import hashlib
import json
from collections import Counter

import numpy as np

import engine as e
import independent as ind


def main():
    data=json.loads((e.HERE/'control-results.json').read_text(encoding='utf8'))
    readings=json.loads((e.HERE/'known-readings.json').read_text(encoding='utf8'))
    observer=e.terminal_observer()
    failures=[]
    for r in data['rows']:
        plain=readings[r['reading']]
        key=e.source.page_seeded_stream(r['source_index'],1124,r['mode'])
        assert r['signed_slope']==r['sign']*(key[1]-key[0])%29
        assert r['signed_intercept']==r['sign']*key[0]%29
        for i,pointer in enumerate(r['used_key_positions']):
            assert (r['cipher'][i]+r['sign']*key[pointer])%29==plain[i]
            if i:
                rejected=pointer-r['used_key_positions'][i-1]-1
                assert rejected in (0,1)
                if rejected:
                    assert (r['cipher'][i-1]-r['cipher'][i])%29==r['signed_slope']
        returned,text,used=ind.decode(r['cipher'],r['signed_slope'],r['signed_intercept'],len(plain),300,e.source.gp.IDX_TO_TRANS)
        assert returned==r['full_indices']
        assert abs(ind.score(text)-r['full_score'])<1e-10
        assert hashlib.sha256(bytes(returned)).hexdigest()==r['full_sha256']
        assert r['full_exact']==(returned==plain)
        assert r['screen_pass']==(r['screen_score']>-6.5)
        assert r['full_pass']==(r['full_score']>-5.5)
        if not r['full_exact']:
            terminal=observer(np.array(r['cipher'],dtype=np.int64),np.array(key,dtype=np.int64),r['sign'],0,len(plain),300)
            ranks=[i+1 for i,state in enumerate(terminal) if list(state[3])==plain]
            truth=e.sweep.Q.score(e.text(plain))
            chosen=e.sweep.Q.score(e.text(returned))
            failures.append({'control_ordinal':r['control_ordinal'],'signed_slope':r['signed_slope'],
                             'reading':r['reading'],'true_final_rank':min(ranks) if ranks else None,
                             'chosen_minus_truth_cumulative':chosen-truth,
                             'chosen_normalized':r['full_score'],'truth_normalized':ind.score(e.text(plain))})
    result={'schema':'page-ramp-independent-controls-v1','control_arrays_checked':112,
            'independent_linear_full_reconstructions':112,'exact_recoveries':sum(r['full_exact'] for r in data['rows']),
            'score_gate_passes':data['both_gate_passes'],'genuine_skip_plants':data['genuine_skip_plants'],
            'nonexact_cases':len(failures),'nonexact_slope_reading_structures':len({(r['signed_slope'],r['reading']) for r in failures}),
            'truth_survives_in_nonexact':sum(r['true_final_rank'] is not None for r in failures),
            'strictly_higher_cumulative_alternatives':sum(r['chosen_minus_truth_cumulative']>1e-10 for r in failures),
            'normalized_worse_alternatives':sum(r['chosen_normalized']<r['truth_normalized'] for r in failures),
            'failures':failures,'limit':'Array arithmetic and eight fixed slope/reading conditions; not independent population-level power or full-search calibration.'}
    e.write(e.HERE/'control-check.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='failures'},indent=2))


if __name__=='__main__':
    main()
