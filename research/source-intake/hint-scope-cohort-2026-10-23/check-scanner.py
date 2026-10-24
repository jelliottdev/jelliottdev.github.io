"""Direct non-FFT match recount, independently of source and producer imports."""
import hashlib,json
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent
p=json.loads((H/'scanner-plan-frozen.json').read_text());r=json.loads((H/'scanner-results.json').read_text())
assert r['plan_sha256']==hashlib.sha256((H/'scanner-plan-frozen.json').read_bytes()).hexdigest()
rng=np.random.default_rng(p['seed']);total=0
for row in r['cases']:
    W=row['window'];off=row['truth_offset'];L=p['corpus_length']
    corpus=rng.integers(1,16,L,dtype=np.int16);fc=rng.integers(0,4,W,dtype=np.int16)
    obs=corpus[off:off+W]+fc
    exact=np.zeros(L-W+1,dtype=np.int64);interval=exact.copy()
    for j in range(W):
        values=corpus[j:j+L-W+1]
        exact+=(values==obs[j]);interval+=((values<=obs[j])&(values>=obs[j]-fc[j]))
    for name,counts in [('exact',exact),('interval',interval)]:
        a=row['patterns'][name]
        assert int(counts.max())==a['best'] and int(counts[off])==a['truth_count']
        assert int(counts[a['blocked_best_offset']])==a['best']
        assert len(counts)==a['offsets']
        assert hashlib.sha256(','.join(map(str,counts.tolist())).encode()).hexdigest()==a['counts_sha256']
        total+=len(counts)
    assert interval[off]==W
print('PASS:',total,'per-offset exact/interval counts independently match; no FFT or source helper imported.')
