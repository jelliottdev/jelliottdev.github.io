"""Offline saved-score and scope consistency checks; no external corpus needed."""
import hashlib,json
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent
def main():
    r=json.loads((H/'results.json').read_bytes());p=json.loads((H/'reproduction/protocol-frozen.json').read_bytes())
    assert r['protocol_sha256']==hashlib.sha256((H/'reproduction/protocol-frozen.json').read_bytes()).hexdigest()
    for f,h in p['pins'].items():assert hashlib.sha256((H/'reproduction'/f).read_bytes()).hexdigest()==h,f
    assert hashlib.sha256((H/'alignment-scores.npz').read_bytes()).hexdigest()==r['score_arrays_sha256']
    total=0;complete=0
    with np.load(H/'alignment-scores.npz') as z:
        assert len(z.files)==108
        for row in r['per_text_winners']:
            v=z[row['key']+'_fft'];i=z[row['key']+'_integer'];w=p['patterns'][row['pattern']]['width'];total+=len(v)
            assert len(v)==row['starts']==row['words']-w+1 and v.shape==i.shape
            assert float(v.max())==row['raw_max'] and int(v.argmax())==row['offset']
            assert int(i.max())==row['integer_max']==int(i[row['offset']])
            assert np.flatnonzero(i==i.max()).tolist()==row['integer_ties']
            assert np.max(np.abs(v-i))<.001 and row['complete']==bool(i.max()==w)
            complete+=row['complete'] and row['pattern'].startswith('real')
    assert total==40245==r['alignment_scores'] and complete==0==r['complete_real_prefix_matches']
    for g in r['groups']:
        for n,b in g['best'].items():
            rows=[x for x in r['per_text_winners'] if x['pattern']==n];best=max(rows,key=lambda x:x['raw_max'])
            assert (best['raw_max'],best['text'],best['offset'])==(b['count'],b['text'],b['offset'])
    print('PASS: frozen hashes, all40,245 saved score pairs, per-text/global selections, ties and zero complete prefixes. This is a saved-evidence check, not an external-input replay.')
if __name__=='__main__':main()
