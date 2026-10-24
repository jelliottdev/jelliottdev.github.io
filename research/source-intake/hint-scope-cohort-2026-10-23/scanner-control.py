"""Fresh bounded controls of the exact L4 blocked FFT scanner; no LP2 scoring."""
import hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent; S=H.parents[3]/'source-cache/dukotah-cicada3301'
base='liber-primus/analysis/round10/L4-skeleton/'
rev='f08b20b632d91209ddbaa747e8e2f23df0c78ba1'
if '--freeze' in sys.argv:
    pins=[]
    for f in ['scanner.py','skel.py']:
        raw=(S/base/f).read_bytes()
        assert raw==subprocess.check_output(['git','-C',str(S),'show',f'{rev}:{base}{f}'])
        pins.append(dict(path=base+f,sha256=hashlib.sha256(raw).hexdigest()))
    plan=dict(revision=rev,source_id='C-01',seed=330120261023,corpus_length=5000,
        windows=[120,400,2928],offsets=['0','2048','L-W'],block=4096,size=8192,
        rules='For each W/offset: generate uniform integers 1..15; add independently seeded 0..3 F counts to planted observed pattern. Run exact and directional-interval source patterns over same corpus. Check every offset against direct independent match counts; interval truth must equal W. This is a synthetic instrument test, not corpus replay.',inputs=pins)
    assert not (H/'scanner-plan-frozen.json').exists()
    (H/'scanner-plan-frozen.json').write_text(json.dumps(plan,indent=2)+'\n')
    print('Frozen L4 synthetic scanner plan'); sys.exit()
p=json.loads((H/'scanner-plan-frozen.json').read_text())
for x in p['inputs']: assert hashlib.sha256((S/x['path']).read_bytes()).hexdigest()==x['sha256']
def load(name):
    spec=importlib.util.spec_from_file_location(name,S/base/(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
sk=load('skel'); scanner=load('scanner'); rng=np.random.default_rng(p['seed']); rows=[]
for W in p['windows']:
    for off in [0,2048,p['corpus_length']-W]:
        corpus=rng.integers(1,16,p['corpus_length'],dtype=np.int16)
        fc=rng.integers(0,4,W,dtype=np.int16); obs=corpus[off:off+W]+fc
        pats=[scanner.Pattern('exact',sk.groups_slack(obs,0),W,p['size']),
              scanner.Pattern('interval',sk.groups_interval(obs,fc),W,p['size'])]
        best,_=scanner.scan_corpus({'synthetic':corpus},pats,block=p['block'],size=p['size'])
        # Preserve scan_block output for every valid offset independently of block joins.
        values=scanner.scan_block(corpus,pats,size=p['size'])
        row=dict(window=W,truth_offset=off,patterns={})
        for name,arr in values.items():
            counts=np.rint(arr).astype(np.int64)
            assert np.max(np.abs(arr-counts))<0.01
            assert abs(best[name][0]-int(counts.max()))<0.01
            assert int(counts[best[name][2]])==int(counts.max())
            if name=='interval': assert counts[off]==W
            row['patterns'][name]=dict(best=int(counts.max()),truth_count=int(counts[off]),
                blocked_best_offset=best[name][2],offsets=len(counts),
                counts_sha256=hashlib.sha256(','.join(map(str,counts.tolist())).encode()).hexdigest())
        rows.append(row)
out=dict(plan_sha256=hashlib.sha256((H/'scanner-plan-frozen.json').read_bytes()).hexdigest(),cases=rows)
(H/'scanner-results.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS: 9 synthetic corpora x 2 matchers; interval plants all recover W at the truth; block and whole-array maxima agree.')
