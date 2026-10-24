"""Independent integer witness checks of the already-saved source T0 outputs."""
import replay as r
import numpy as np
C=r.verify();P=r.read('inputs-frozen.json')['manuscript']['words']
assert r.sha((r.H/'replay-controls-frozen.py').read_bytes())==r.read('controls-plan-frozen.json')['runner_sha256']
names=sorted(C,key=lambda k:-len(C[k]));sources=[]
for want in ['kjv','emerson','hermetic','blake','dhammapada']:
    found=next((n for n in names if want in n.lower() and len(C[n])>4*P),None)
    if found:sources.append(found)
sources=sources[:3];assert sources==['data/kjv.txt','keys/emerson_essays_first_series.txt']
rng=np.random.default_rng(3301);patterns={};truth={}
for si,name in enumerate(sources):
    off=int(rng.integers(0,len(C[name])-P));base=C[name][off:off+P]
    order=rng.permutation(P);fc=np.zeros(P,dtype=np.int16)
    # Independent explicit histogram, equivalent to the source's n=2928 scaling.
    fc[order[:387]]=1;fc[order[387:421]]=2;fc[order[421:422]]=3
    obs=base+fc;truth[f'T0_{si}']={'text':name,'offset':off}
    patterns[f'T0_{si}']=(obs,fc)
    if si==0:
        sh=rng.permutation(P);patterns['T0null']=(obs[sh],fc[sh])
rows=[]
for result in r.read('positive_control_T0.json')['results']:
    tag,mode=result['pattern'].split(':');obs,fc=patterns[tag]
    a=C[result['text']][result['offset']:result['offset']+P]
    n=int((a==obs).sum()) if mode=='exact' else int(((a>=obs-fc)&(a<=obs)).sum())
    assert abs(n-result['best'])<.01
    if tag in truth:
        assert result['truth']==truth[tag]
        assert (result['text'],result['offset'])==(truth[tag]['text'],truth[tag]['offset'])
    rows.append(dict(pattern=result['pattern'],integer_count=n,text=result['text'],offset=result['offset'],exact_planted_location=(tag in truth)))
r.write('independent-t0-audit.json',dict(output_sha256=r.sha((r.H/'positive_control_T0.json').read_bytes()),source_selected_plants=len(sources),histogram=[2506,387,34,1],null_f_total=458,witnesses=rows,limit='Checks saved winners and exact plant locations, not independent exhaustive corpus maxima. One shuffled T0 pattern is not a calibrated null distribution; no historical z-threshold pass is claimed.'))
print('PASS: six saved T0 witnesses; four exact planted-location recoveries.')
