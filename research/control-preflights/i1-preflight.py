"""Read-only control replay and source-grid accounting for pinned Round 19/I1."""
import hashlib
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--source-root',type=Path,required=True)
parser.add_argument('--output',type=Path,default=HERE/'dukotah-i1-control-receipt.json')
args=parser.parse_args()
SRC = args.source_root.resolve()
I1 = SRC / 'liber-primus/analysis/round19/I1'
sys.path.insert(0, str(I1))
import driftbeam as db
import constructions as cx
import run_gates as gates

files = [
    'liber-primus/analysis/round19/I1/driftbeam.py',
    'liber-primus/analysis/round19/I1/constructions.py',
    'liber-primus/analysis/round19/I1/run_gates.py',
    'liber-primus/analysis/round19/I1/run_fp.py',
    'liber-primus/analysis/round19/I1/test_driftbeam.py',
    'liber-primus/analysis/campaign18_skip/skipdecode.py',
    'liber-primus/analysis/round18/L2-filter-leak/fastbeam.py',
    'liber-primus/analysis/round19/I1/out_fix.json',
    'liber-primus/analysis/round19/I1/out_fp_deep.json',
    'liber-primus/analysis/round19/I1/out_fp_deep2.json',
    'liber-primus/analysis/round19/I1/out_fp_curve.json',
]
fingerprints = {p: hashlib.sha256((SRC / p).read_bytes()).hexdigest() for p in files}
rev = subprocess.check_output(['git','-C',str(SRC),'rev-parse','HEAD'],text=True).strip()
assert rev == 'f08b20b632d91209ddbaa747e8e2f23df0c78ba1'
for path,digest in fingerprints.items():
    pinned=subprocess.check_output(['git','-C',str(SRC),'show',f'{rev}:{path}'])
    assert hashlib.sha256(pinned).hexdigest()==digest, f'working file differs from pinned source: {path}'

eq={'gate_EQ':db.gate_EQ(reps=8,lengths=(60,120,400),seed=20260826,verbose=False),
    'gate_EQ2':db.gate_EQ_fast(reps=6,lengths=(120,400),seed=7,verbose=False)}
assert eq['gate_EQ']['pass'] and eq['gate_EQ']['cases']==24 and eq['gate_EQ']['path_mismatches']==0
assert eq['gate_EQ2']['pass'] and eq['gate_EQ2']['cases']==12 and eq['gate_EQ2']['path_mismatches']==0

# Reconstruct the source's visible plant without running driftbeam.py (which writes out_eq.json).
P=cx.take_plain(240,0)
K=cx.key_sha(240*6+1024)
C,info=cx.enc_skip_by_two(P,K,supp=0.83,seed=3301)
plant={}
for name,kw in [('repo_exact',db.PRESETS['exact']),('repo_exact_ms8',db.PRESETS['exact_ms8']),('pair',db.PRESETS['pair']),('drift',db.PRESETS['drift'])]:
    got=db.beam_decode(C,K,sign=-1,o=0,beam_w=400,**kw)
    plant[name]={'score':got['score'],'rune_recovery':db.recovery(got['plain_idx'],P),'n_skips':got['n_skips']}
assert info['n_skips']==6
assert plant['pair']['rune_recovery']==plant['drift']['rune_recovery']==1
assert plant['repo_exact']['rune_recovery']<0.5

fix=json.loads((I1/'out_fix.json').read_text(encoding='utf-8'))
deep=json.loads((I1/'out_fp_deep.json').read_text(encoding='utf-8'))
deep2=json.loads((I1/'out_fp_deep2.json').read_text(encoding='utf-8'))
curve=json.loads((I1/'out_fp_curve.json').read_text(encoding='utf-8'))
fix_pred=sum(len(gates.fix_cases(L))*len(fix['modes'])*fix['n_seeds'] for L in fix['lengths'])
fix_gate_pred=sum(sum(x[-1] for x in gates.fix_cases(L))*len(fix['modes'])*fix['n_seeds'] for L in fix['lengths'])
assert fix_pred==len(fix['rows'])==2100
assert fix_gate_pred==1400
assert len(deep['rows'])==len(deep['summary'])*deep['n_per_setting']==20000
assert len(deep2['rows'])==len(deep2['summary'])*deep2['n_per_setting']==8000
assert len(curve['rows'])==len(curve['summary'])*curve['n_per_setting']==6000
assert len({(r['null'],r['mode'],r['trial']) for r in deep['rows']})==len(deep['rows'])
assert len({(r['null'],r['mode'],r['trial']) for r in deep2['rows']})==len(deep2['rows'])
assert len({(r['null'],r['mode'],r['trial']) for r in curve['rows']})==len(curve['rows'])
assert len({(r['null'],r['mode'],r['trial']) for d in (deep,deep2,curve) for r in d['rows']})==34000

receipt={
    'schema':'dukotah-i1-control-and-count-v1',
    'source_revision':rev,
    'source_ids_supported':['I1-03','I1-06','I1-09','R19-I3-NULLS','R20-P3-PANELMAX-SEEDPRIOR-DRIFT','R20-HITFN-RECOVERY-GATE'],
    'scope':'I1 decoder parity and one synthetic plant; source-grid row accounting only. No real LP2 candidate was scored in this replay.',
    'source_files_sha256':fingerprints,
    'fresh_control':{'g_eq':{k:v for k,v in eq['gate_EQ'].items()},'g_eq2':{k:v for k,v in eq['gate_EQ2'].items()},'plant':{'length':len(P),'source_rejections':info['n_skips'],'modes':plant}},
    'source_grid_accounting':{
        'fix':{'predicted_rows':fix_pred,'stored_rows':len(fix['rows']),'gate_tagged_rows':fix_gate_pred,'modes':len(fix['modes']),'lengths':fix['lengths'],'seeds_per_setting':fix['n_seeds']},
        'wrong_key_deep':{'settings':len(deep['summary']),'per_setting':deep['n_per_setting'],'stored_rows':len(deep['rows'])},
        'wrong_key_deep2':{'settings':len(deep2['summary']),'per_setting':deep2['n_per_setting'],'stored_rows':len(deep2['rows'])},
        'wrong_key_curve':{'settings':len(curve['summary']),'per_setting':curve['n_per_setting'],'stored_rows':len(curve['rows'])},
        'wrong_key_total_rows':len(deep['rows'])+len(deep2['rows'])+len(curve['rows'])
    },
    'limits':['Source G-FP rows and G-FIX rows were counted and checked for unique setting/trial IDs, not recomputed here.','The test suite exercises shared decoder logic; I3/P3 null thresholds and HITFN are not independently replayed by this receipt.','No unsolved LP2 plaintext recovery claim.']
}
out=args.output.resolve()
out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(out)
