"""Independent finite-alias checks and only the 36 failed plant diagnostics.

No manuscript arrays or target ledger are read. No owner-record files written.
"""
import collections,hashlib,importlib.util,json,random,sys,time
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];RECORD=ROOT/'experiments/records/fibonacci-stream-skip-grid'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fib(a,b,n=1176):
 values=[a,b]
 while len(values)<n:values.append((values[-1]+values[-2])%29)
 return values[:n]
def main():
 started=time.perf_counter();files=['engine.py','prove.py','proof-receipt.json','aliases.json','preflight-plan.json','preflight.py','parity-results.json','control-results.json','preflight-independent-check.json']
 hashes={name:sha(RECORD/name) for name in files}
 aliases=json.loads((RECORD/'aliases.json').read_text());keys={(a,b):fib(a,b) for a in range(29) for b in range(29)};multiplicity=collections.Counter()
 for r in aliases:
  a,b=r['a'],r['b']
  for _ in range(r['offset']):a,b=b,(a+b)%29
  mapped=(r['sign']*a%29,r['sign']*b%29);assert mapped==(r['canonical_a'],r['canonical_b'])
  original=keys[r['a'],r['b']];assert keys[mapped][:1176-r['offset']]==[(r['sign']*v)%29 for v in original[r['offset']:]]
  multiplicity[mapped]+=1
 assert len(aliases)==8410 and len(multiplicity)==841 and set(multiplicity.values())=={10}
 # Maximum last consumed index: offset + four advances for each transition.
 assert 4+4*(277-1)==1108 and 4+4*277+8==1120<1176
 controls=json.loads((RECORD/'control-results.json').read_text());readings=json.loads((RECORD/'known-readings.json').read_text());failures=[r for r in controls['rows'] if r['eligible'] and not r['full_exact']];assert len(failures)==36
 sys.path.insert(0,str(RECORD));spec=importlib.util.spec_from_file_location('fib_owner_engine',RECORD/'engine.py');engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine);observer=engine.terminal_observer();rows=[]
 for r in failures:
  pair=(r['a'],r['b']);K=keys[pair];P=readings[r['reading']];rng=random.Random(r['seed']);C=[];sk=[];used=[];j=0;previous=None
  for value in P:
   count=0
   while True:
    c=(value-K[j])%29
    if previous is not None and c==previous and rng.random()<.83:j+=1;count+=1;continue
    break
   C.append(c);sk.append(count);used.append(j);j+=1;previous=c
  assert C==r['cipher'] and sk==r['skips'] and used==r['used_key_positions'] and max(sk)<=3
  valid=True
  for i in range(1,len(P)):
   for rejected in range(used[i-1]+1,used[i]):
    if (P[i]-K[rejected])%29!=C[i-1]:valid=False
  assert valid
  states=observer(np.array(C,np.int64),np.array(K,np.int64),1,0,len(P),200)
  winner=max(states,key=lambda x:x[0]);assert list(winner[3])==r['returned_indices'];assert hashlib.sha256(bytes(winner[3])).hexdigest()==r['returned_sha256']
  truths=[(index,state) for index,state in enumerate(states,1) if list(state[3])==P]
  truthraw=engine.sweep.Q.score(engine.text(P));truthnorm=engine.sweep.Q.score_norm(engine.text(P));chosenraw=engine.sweep.Q.score(winner[2]);chosennorm=engine.sweep.Q.score_norm(winner[2]);delta=chosenraw-truthraw
  assert abs(chosennorm-r['full_score'])<2e-12
  rows.append({'a':pair[0],'b':pair[1],'reading':r['reading'],'seed':r['seed'],'skip_total':sum(sk),'skip_max':max(sk),'true_path_valid':valid,'genuine_skips':sum(sk)>0,'true_plaintext_survives':bool(truths),'first_truth_rank':truths[0][0] if truths else None,'truth_state_count':len(truths),'terminal_candidates':len(states),'classification':'tie' if abs(delta)<1e-10 else ('strictly_higher_alternative' if delta>0 else 'lower_scoring_alternative'),'truth_cumulative':truthraw,'chosen_cumulative':chosenraw,'cumulative_delta':delta,'truth_normalized':truthnorm,'chosen_normalized':chosennorm,'chosen_normalized_below_truth':chosennorm<truthnorm-1e-12,'changed_positions':[i for i,(x,y) in enumerate(zip(P,winner[3])) if x!=y]})
 result={'scope':'Independent finite-key alias verification plus diagnostics of exactly36 pre-existing synthetic control mismatches. No manuscript target or all841control rerun.','owner_input_hashes':hashes,'auditor_sha256':sha(Path(__file__)),'alias_mappings_independently_checked':len(aliases),'canonical_pairs':len(multiplicity),'preimages_each':10,'aligned_finite_prefix_min':1172,'max_consumed_index':1108,'max_padding_need':1120,'key_length':1176,'tie_proof':'Induct on path length with pointer translation j->j-offset. Signed shifted key values match, so plaintext, rejected-key constraints, cumulative score and extension order match. Python sort uses only cumulative score and is stable; first max is stable. No pointer penalty or padding divergence. Thus ordered terminal candidates and all winner ties are preserved, not only score maxima. Original source-label ordinal preserves which alias wins ties.','failure_count':len(rows),'classifications':dict(collections.Counter(r['classification'] for r in rows)),'true_survivors':sum(r['true_plaintext_survives'] for r in rows),'genuine_skip_failures':sum(r['genuine_skips'] for r in rows),'truth_rank_min':min(r['first_truth_rank'] for r in rows if r['first_truth_rank']),'truth_rank_max':max(r['first_truth_rank'] for r in rows if r['first_truth_rank']),'chosen_normalized_below_truth':sum(r['chosen_normalized_below_truth'] for r in rows),'rows':rows,'elapsed_seconds':time.perf_counter()-started}
 assert all(sha(RECORD/name)==value for name,value in hashes.items())
 (HERE/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['rows','owner_input_hashes','tie_proof']},indent=2))
if __name__=='__main__':main()
