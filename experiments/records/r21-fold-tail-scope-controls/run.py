"""Execute exact source fold definitions with actual source beam, without panel scoring."""
import ast,dataclasses,hashlib,json,random,sys,types,typing
from pathlib import Path
HERE=Path(__file__).resolve().parent;LP=HERE/'source/liber-primus'
sys.dont_write_bytecode=True
sys.path.insert(0,str(LP/'analysis/round19/I1'))
import driftbeam as DB
import skipdecode as SK
def definitions(path,names,ns):
    tree=ast.parse(path.read_text(encoding='utf-8'));tree.body=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
    assert {n.name for n in tree.body}==names
    exec(compile(tree,str(path),'exec'),ns)
def load_helpers():
    ns={'dataclass':dataclasses.dataclass,'field':dataclasses.field,'Sequence':typing.Sequence,'Optional':typing.Optional,'DB':DB,'List':typing.List}
    definitions(LP/'analysis/round20/HITFN/hitfn20.py',{'HitDecode','_heldout_recovery'},ns)
    ns['H']=types.SimpleNamespace(HitDecode=ns['HitDecode'],_heldout_recovery=ns['_heldout_recovery'])
    ns.update(RECOVERY_BAR=.9,AGREE_RULES=('min','mean','frac_pass'))
    definitions(LP/'analysis/round21/L1-seal-realmode-proxy/hitfn21_folds.py',{'_fold_bounds','_one_fold_heldout','heldout_recovery_folds'},ns)
    return ns
def generate():
    for p in json.loads((HERE/'source-manifest.json').read_text())['files']:
        assert hashlib.sha256((HERE/p['path']).read_bytes()).hexdigest()==p['sha256']
    plan=json.loads((HERE/'plan.json').read_text());P=json.loads((HERE/'plain.json').read_text())['plain_idx'];assert len(P)==240
    ns=load_helpers();plants=[];rows=[]
    real_beam=DB.beam_decode
    for seed in plan['seeds']:
        rng=random.Random(seed);K=[rng.randrange(29) for _ in range(2000)]
        for supp in plan['suppression']:
            C,nsk,_=SK.encipher_keyskip(P,K,sign=-1,supp=supp,seed=seed+100)
            full=real_beam(C,K,sign=-1,o=0,beam_w=400,want_path=True,**DB.PRESETS['exact']);F=full['plain_idx']
            plants.append({'seed':seed,'suppression':supp,'cipher_idx':C,'key_idx':K,'truth_idx':P,'full_idx':F,'full_recovery':DB.recovery(F,P),'encoder_skips':nsk})
            dec=ns['HitDecode'](C,K);assert dec.truth_idx is None
            for k in plan['fold_counts']:
                bounds=ns['_fold_bounds'](240,k);folds=[]
                for lo,hi in bounds:
                    calls=[]
                    def traced(*args,**kwargs):
                        out=real_beam(*args,**kwargs)
                        calls.append({'cipher_idx':list(args[0]),'offset':kwargs['o'],'plain_idx':out['plain_idx'],'ptr_end':out['ptr_end']})
                        return out
                    DB.beam_decode=traced
                    try:rec=ns['_one_fold_heldout'](dec,F,lo,hi)
                    finally:DB.beam_decode=real_beam
                    if rec is None:
                        blind=wrong=None
                    else:
                        # Same actual decode, exact helper applied to diagnostic references.
                        blindref=[(x+1)%29 if i<40 else x for i,x in enumerate(F)]
                        wrongref=[(x+1)%29 for x in F]
                        blind=ns['_one_fold_heldout'](dec,blindref,lo,hi)
                        wrong=ns['_one_fold_heldout'](dec,wrongref,lo,hi)
                    folds.append({'lo':lo,'hi':hi,'recovery':rec,'head40_changed_recovery':blind,'all_changed_recovery':wrong,'calls':calls})
                aggregations={}
                for rule in plan['rules']:
                    value=ns['heldout_recovery_folds'](dec,F,k_folds=k,agree_rule=rule)
                    aggregations[rule]=value
                rows.append({'seed':seed,'suppression':supp,'k':k,'folds':folds,'aggregations':aggregations})
    return {'schema':'source-fold-tail-controls-v1','plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),'plants':plants,'rows':rows,'interpretation':'Six newly enciphered known-key plants; source fold helpers and beam only, no panel score, survivor selection or source catch-rate replay.'}
if __name__=='__main__':
    result=generate();(HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: six plants, 30 k-grid rows, source helpers executed')
