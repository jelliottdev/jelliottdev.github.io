"""Bounded exact-source LENGTH replay, with upper as well as lower endpoint."""
import hashlib, importlib.util, json, re
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[3] / 'source-cache/dukotah-cicada3301'
plan = json.loads((HERE/'plan-frozen.json').read_text())
for p in plan['inputs']:
    assert hashlib.sha256((SOURCE/p['path']).read_bytes()).hexdigest() == p['sha256']
spec=importlib.util.spec_from_file_location('exact_length', SOURCE/'liber-primus/analysis/skeleton/length_anomaly.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert [m.enc(w) for w in m.PARABLE_EN] == m.PARABLE_RUNES
assert all(x < 4.26844262295082 for x in np.array([4]*30,dtype=float))
assert all(x >= 4.424863387978142 for x in np.array([5]*30,dtype=float))
lp,F=m.words_of(range(55)); n=len(lp); lo=float(lp.mean()-F/n); hi=float(lp.mean())
rows=[]
for p in plan['inputs']:
    name=p['path']
    if not (name.endswith('/kjv.txt') or '/data/keys/' in name): continue
    text=(SOURCE/name).read_text(encoding='utf-8',errors='ignore')
    v=np.array([x for x in (m.enc(w) for w in re.findall(r"[A-Za-z']+",text)) if x])
    if len(v)<n*2:
        rows.append(dict(path=name,words=len(v),eligible=False)); continue
    cs=np.concatenate([[0],np.cumsum(v)])
    idx=np.arange(0,len(v)-n,max(1,(len(v)-n)//4000))
    sums=cs[idx+n]-cs[idx]; wm=sums/n
    rows.append(dict(path=name,words=len(v),eligible=True,sampled_passages=len(idx),
        first_offset=int(idx[0]),last_offset=int(idx[-1]),step=max(1,(len(v)-n)//4000),
        mean=float(v.mean()),minimum=float(wm.min()),maximum=float(wm.max()),
        lower_reaching=int((wm>=lo).sum()),upper_reaching=int((wm>=hi).sum()),
        sampled_sums_sha256=hashlib.sha256(','.join(map(str,sums.tolist())).encode()).hexdigest()))
out=dict(plan_sha256=hashlib.sha256((HERE/'plan-frozen.json').read_bytes()).hexdigest(),
    controls={'parable_exact':20,'constant4_below_both':True,'constant5_above_both':True},
    lp2={'words':n,'runes':int(lp.sum()),'F':F,'lower':lo,'upper':hi},rows=rows)
(HERE/'length-results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2))
