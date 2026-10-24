"""Verify declared bytes and saved source selection bookkeeping without external text."""
import hashlib,json
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run():
    record=json.loads((H/'record.json').read_bytes())
    for row in record['reproduction']['inputs']+record['reproduction']['outputs']:
        prefix='experiments/records/'+record['id']+'/'
        assert row['path'].startswith(prefix)
        assert sha(H/row['path'][len(prefix):])==row['sha256'],row['path']
    r=H/'reproduction';d=json.loads((r/'results.json').read_bytes());s=np.load(r/'screen-scores.npy');v=np.load(r/'phase-selections.npy');words=json.loads((r/'keywords-frozen.json').read_bytes())
    # Vocabulary export is a source-order list of (label, encoded array).
    if isinstance(words,dict):words=words.get('keywords',words.get('words'))
    assert s.shape==(55,11256) and np.isfinite(s).all()
    assert v.shape==(55,623,2,2,2)
    for page in range(55):
        ix=0
        for j,row in enumerate(words):
            key=row['key']
            for sign in range(2):
                for atb in range(2):
                    block=s[page,ix:ix+len(key)];o=int(np.argmax(block));assert np.array_equal(v[page,j,sign,atb],(o,block[o]));ix+=len(key)
        assert ix==11256
        assert d['page_results'][page]['best_screen'][0]==float(s[page].max())
    assert d['screens']==s.size==619080 and d['phase_selections']==137060
    assert d['full_promotions']==int((v[...,1]>-6).sum())==0
    assert json.loads((r/'full-survivors.json').read_bytes())==[]
    assert d['best_screen']['score']==float(s.max())
    controls=json.loads((r/'controls-results.json').read_bytes());domain=[x for x in controls['controls'] if x['group']=='domain'];summary=json.loads((H/'control-summary.json').read_bytes())
    assert len(domain)==617 and sum(x['full_gate'] for x in domain)==617 and sum(x['exact_recovery'] for x in domain)==575
    assert sum(x['exact_output_found'] for x in controls['full_grids'])==3
    assert summary['known_key']==dict(total=617,score_passes=617,exact_recoveries=575)
    print('PASS: declared bytes, all 619,080 scores/137,060 selections, zero promotions, and control counts')
if __name__=='__main__':run()
