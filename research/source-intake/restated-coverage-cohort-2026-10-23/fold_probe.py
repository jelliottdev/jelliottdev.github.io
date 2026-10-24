import ast,dataclasses,json,random,sys,types,typing
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];LP=ROOT.parent/'source-cache/dukotah-cicada3301/liber-primus'
sys.path.insert(0,str(LP/'analysis/round19/I1'))
import driftbeam as DB
from lp import gematria as gp
def definitions(path,names,ns):
    tree=ast.parse(path.read_text());tree.body=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
    exec(compile(tree,str(path),'exec'),ns)
ns={'dataclass':dataclasses.dataclass,'field':dataclasses.field,'Sequence':typing.Sequence,'Optional':typing.Optional,'DB':DB,'List':typing.List}
definitions(LP/'analysis/round20/HITFN/hitfn20.py',{'HitDecode','_heldout_recovery'},ns)
ns['H']=types.SimpleNamespace(HitDecode=ns['HitDecode'],_heldout_recovery=ns['_heldout_recovery'])
ns.update(RECOVERY_BAR=.9,AGREE_RULES=('min','mean','frac_pass'))
definitions(LP/'analysis/round21/L1-seal-realmode-proxy/hitfn21_folds.py',{'_fold_bounds','_one_fold_heldout','heldout_recovery_folds'},ns)
P=json.loads((ROOT/'experiments/records/c2-extension-generator-controls/fixtures.json').read_text())['cases'][0]['plain']
for seed in [3301]:
    r=random.Random(seed);K=[r.randrange(29) for _ in range(2000)];C=[(p+k)%29 for p,k in zip(P,K)]
    full=DB.beam_decode(C,K,sign=-1,o=0,beam_w=400,want_path=True,**DB.PRESETS['exact'])
    dec=ns['HitDecode'](C,K)
    print('full',DB.recovery(full['plain_idx'],P),flush=True)
    rows=[]
    for k in [2,3,4,5,6]:
        recs=[ns['_one_fold_heldout'](dec,full['plain_idx'],lo,hi) for lo,hi in ns['_fold_bounds'](len(C),k)]
        rows.append({'k':k,'fold_recoveries':recs}); print(rows[-1],flush=True)
