"""Check saved outputs and source-normalized scores; no external manuscript required."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H/'reproduction'))
import engine as e
def main():
    record=json.loads((H/'record.json').read_bytes());prefix='experiments/records/autokey-skip-family/'
    for role in ('inputs','outputs'):
        for row in record['reproduction'][role]:
            assert row['path'].startswith(prefix)
            assert hashlib.sha256((H/row['path'][len(prefix):]).read_bytes()).hexdigest()==row['sha256'],row['path']
    r=H/'reproduction';d=json.loads((r/'results.json').read_bytes())
    with np.load(r/'measurements.npz') as archive:z={name:archive[name] for name in archive.files}
    shape=(55,45,2,2)
    assert z['scores'].shape==shape and np.isfinite(z['scores']).all()
    assert d['cases']==9900 and d['source_hits']==int((z['scores']> -5.5).sum()) and d['normalized_terminal_hits']==int((z['terminal_max']> -5.5).sum())
    for ix in np.ndindex(shape):
        L=z['lengths'][ix[0]]
        for name,score in (('source_winner',z['scores'][ix]),('normalized_winner',z['terminal_max'][ix])):
            path=z[name][ix];assert ((path[:L]>=0)&(path[:L]<29)).all() and (path[L:]==-1).all()
            assert e.Q.score_norm(e.text(path[:L]))==score,(ix,name)
        assert 1<=z['terminal_rank'][ix]<=z['terminal_count'][ix]<=450
        assert z['terminal_max'][ix]>=z['scores'][ix]
    controls=json.loads((r/'controls-results.json').read_bytes());assert len(controls['domain'])==360
    for mode,expected in (('P',54),('C',59)):
        rows=[x for x in controls['domain'] if x['mode']==mode]
        assert len(rows)==180 and sum(x['exact_recovery'] for x in rows)==expected and sum(x['truth_feasible'] for x in rows)==expected
    assert sum(not x['truth_feasible'] for x in controls['domain'])==247
    print('PASS: declared bytes, all 9,900 source/normalized winning-output scores, strict gates and control counts')
if __name__=='__main__':main()
