"""Independent synthetic scorer/count/packing checks; no target values loaded."""
import sys,argparse,json,math,hashlib,ast,random,copy
from pathlib import Path
from fractions import Fraction
sys.dont_write_bytecode=True
import numpy as np
import oracle as O
H=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--producer-root',required=True,type=Path);p.add_argument('--source-root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();assert not a.output.exists();sys.path.insert(0,str(a.producer_root));import engine as E
 rng=random.Random(241024021);fixtures=[]
 fixtures.append([[int((i*7+j)%29) for i in range(n)] for j,n in enumerate([17,22,19,25,20,16])])
 fixtures.append([[rng.randrange(29) for _ in range(n)] for n in [37,29,43,31,40,25]])
 fixtures.append([[int(x) for x in E.filtered(n,3301+j)] for j,n in enumerate([57,64,71,59,83,76])])
 fixtures.append([[int((i%2)*7) for i in range(n)] for n in [23,31,17,29]])
 fixtures.append([[0],[1,2],[3]*17,[4]*19])
 point_count=0;max_point=0.;max_sum=0.;max_rate=0.;query_cells=0
 for pages in fixtures:
  actual=E.score(pages,return_losses=True);expected_page=np.zeros((len(pages),16));expected_folds=[]
  for fold in (0,1):
   train=[p for j,p in enumerate(pages) if j%2!=fold];ids=[j for j,p in enumerate(pages) if j%2==fold and len(p)>8];test=[pages[j] for j in ids];model=O.fit(train,8);frozen=copy.deepcopy(model)
   q,y=E.query_counts([np.array(p,dtype=np.uint8) for p in train],[np.array(p,dtype=np.uint8) for p in test]);qi=0;expected=[]
   for j in ids:
    page=pages[j]
    for i in range(8,len(page)):
     history=page[max(0,i-8):i];truth=page[i];row=[]
     for k in range(9):
      counts=model.get(tuple(history[-k:]) if k else (),{})
      assert q[qi,k].tolist()==[counts.get(x,0) for x in range(29)];query_cells+=29
     for kind in ['kt','ppm']:
      for k in range(1,9):row.append(-math.log2(float((O.kt if kind=='kt' else O.ppm)(model,history,truth,k))))
     assert truth==int(y[qi]);qi+=1;expected.append(row);expected_page[j]+=row
   assert model==frozen
   expected=np.array(expected,dtype=float).reshape((-1,16));native=actual['losses'][fold]
   assert native.shape==expected.shape
   error=float(np.max(np.abs(native-expected))) if len(expected) else 0.;assert error<1e-12;max_point=max(max_point,error);point_count+=expected.size
   expected_folds.append(expected.sum(axis=0));error=float(np.max(np.abs(expected_folds[-1]-actual['folds'][fold]['loss_sums'])));assert error<1e-9;max_sum=max(max_sum,error)
  for j,page in enumerate(pages):
   if len(page)<=8:assert actual['page_loss_sums'][j] is None
   else:
    error=float(np.max(np.abs(np.array(actual['page_loss_sums'][j])-expected_page[j])));assert error<1e-9;max_sum=max(max_sum,error)
  total=sum(max(0,len(p)-8) for p in pages);expected=sum(expected_folds)/total
  error=float(np.max(np.abs(np.array(actual['bits_per_rune'])-expected)));assert error<1e-12;max_rate=max(max_rate,error);assert total==actual['scored_positions']
 # Explicit closed full alphabet and after-exclusion closure.
 root={x:x+1 for x in range(29)};high={x:x+1 for x in range(10)};model={():root,(7,):high}
 assert sum(O.ppm(model,[7],x,1) for x in range(29))==1
 assert O.ppm(model,[7],28,1)==Fraction(10,65)*Fraction(29,sum(root[x] for x in range(10,29)))
 q=np.zeros((29,9,29),dtype=np.int32)
 for i in range(29):
  q[i,0]=np.arange(1,30)
  for k in range(1,9):q[i,k,:10]=np.arange(1,11)
 losses=E.ppm_losses(q,np.arange(29));probabilities=2.**(-losses)
 assert np.allclose(probabilities.sum(axis=0),1.,atol=1e-14,rtol=0)
 for k in range(8):
  # All higher contexts have the same support: lower empty-after-exclusion
  # levels must not steal probability before the root's closed remaining set.
  assert np.allclose(probabilities[:,k],probabilities[:,0],atol=1e-15,rtol=0)
 # Highest-context full29 support closes escape immediately.
 qfull=np.tile(np.arange(1,30,dtype=np.int32),(29,9,1));fullprob=2.**(-E.ppm_losses(qfull,np.arange(29)))
 assert np.allclose(fullprob,np.tile((np.arange(1,30)/435.)[:,None],(1,8)),atol=1e-15,rtol=0)
 # Change a future heldout symbol: probabilities before it cannot change.
 train=[np.array([i%29 for i in range(80)],dtype=np.uint8)];test=[np.array([(i*3)%29 for i in range(70)],dtype=np.uint8)]
 q0,y0=E.query_counts(train,test);changed=[test[0].copy()];changed[0][40]=(int(changed[0][40])+1)%29;q1,y1=E.query_counts(train,changed)
 assert np.array_equal(q0[:32],q1[:32]) and np.array_equal(y0[:32],y1[:32])
 # No cross-page context: [1]->2 is absent from two training pages.
 q,_=E.query_counts([np.array([0,1],dtype=np.uint8),np.array([2,3],dtype=np.uint8)],[np.array([7]*8+[1,2],dtype=np.uint8)])
 assert q[1,1].sum()==0
 source=a.source_root/'liber-primus/analysis/recon/i6_mdl/mdl_test.py';tree=ast.parse(source.read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='pack_bytes');ns={'N_SYM':29};exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(source)+'#pack_bytes-only','exec'),ns)
 pack_cases=0
 for n in [0,1,2,61,12956]:
  for mode in ['zeros','random','leadingzeros']:
   seq=[rng.randrange(29) for _ in range(n)] if mode!='zeros' else [0]*n
   if mode=='leadingzeros':seq[:min(9,n)]=[0]*min(9,n)
   assert E.pack(seq)==ns['pack_bytes'](seq)[1];pack_cases+=1
 r=dict(engine_sha256=hashlib.sha256((a.producer_root/'engine.py').read_bytes()).hexdigest(),oracle_sha256=hashlib.sha256((H/'oracle.py').read_bytes()).hexdigest(),checker_sha256=hashlib.sha256((H/'check_engine.py').read_bytes()).hexdigest(),fixtures=len(fixtures),per_symbol_predictive_losses_checked=point_count,training_query_count_cells_checked=query_cells,maximum_point_loss_error=max_point,maximum_aggregate_sum_error=max_sum,maximum_bits_per_rune_error=max_rate,closed_alphabet_and_exclusion_normalized=True,highest_context_all29_normalized=True,future_symbol_does_not_change_earlier_predictions=True,page_boundaries_do_not_form_training_contexts=True,test_counts_not_updated=True,source_packing_cases=pack_cases,target_loaded_or_scored=False)
 a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
