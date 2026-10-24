"""Independent scalar family-rank and provenance invariant checks; synthetic only."""
import sys,math,random,argparse,json,hashlib
from pathlib import Path
from collections import Counter
sys.dont_write_bytecode=True
import numpy as np
H=Path(__file__).resolve().parent

def scalar(rows,tails):
 n=len(rows);m=len(tails);z=[[0.]*m for _ in rows];constants=[]
 for j,tail in enumerate(tails):
  values=[(-1 if tail=='lower' else 1)*row[j] for row in rows]
  if all(v==values[0] for v in values):constants.append(j);continue
  mean=math.fsum(values)/n;sd=math.sqrt(math.fsum((v-mean)**2 for v in values)/n)
  for i,v in enumerate(values):z[i][j]=(v-mean)/sd
 scores=[max(row) for row in z];rank=sum(v>=scores[-1] for v in scores)
 return scores,rank,constants

def provenance_scalar(values,widths):
 n=len(values);out=[]
 for w in widths:
  total=0
  for i in range(n-w+1):
   c=Counter(values[i:i+w]);total+=sum(v*v for v in c.values())
  out.append(29*total/(w*(n-w+1))-w)
 global_counts=Counter(values)
 for bins in [4,8]:
  cuts=[n*j//bins for j in range(bins+1)];sizes=[cuts[j+1]-cuts[j] for j in range(bins)];tables=[Counter(values[cuts[j]:cuts[j+1]]) for j in range(bins)]
  out.append(math.fsum((tables[b][s]-sizes[b]*count/n)**2/(sizes[b]*count/n) for b in range(bins) for s,count in global_counts.items()))
  if bins==8:
   centers=[(cuts[b]+cuts[b+1]-1)/2 for b in range(bins)];center=math.fsum(a*b for a,b in zip(sizes,centers))/n;weights=[c-center for c in centers];variance=math.fsum(size*w*w for size,w in zip(sizes,weights))
   trend=math.fsum(math.fsum(weights[b]*tables[b][s] for b in range(bins))**2/(count/n*variance) for s,count in global_counts.items())
 return out+[trend]

def main():
 p=argparse.ArgumentParser();p.add_argument('--producer-root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();assert not a.output.exists();sys.path.insert(0,str(a.producer_root));import calibration as C,provenance as P
 rng=random.Random(241024022);cases=[]
 cases.append(([[rng.uniform(-3,5) for _ in range(26)] for _ in range(31)],['lower']*18+list(P.TAILS)))
 cases.append(([[4.895261102191]*26 for _ in range(1001)],['lower']*18+list(P.TAILS)))
 cases.append(([[float(i%7),float(i%3),2.] for i in range(120)]+[[1000.,1000.,2.]],['upper','upper','upper']))
 cases.append(([[float(i),float(100-i)] for i in range(1000)]+[[1e9,1e9]],['upper','upper']))
 maxerr=0.
 for rows,tails in cases:
  actual=C.compare(rows[:-1],rows[-1],tails);scores,rank,constants=scalar(rows,tails)
  assert actual['family_rank']==rank and actual['family_reference_rows']==len(rows) and actual['family_rank_fraction']==rank/len(rows)
  assert actual['constant_metrics']==constants
  error=max(abs(a-b) for a,b in zip(scores,actual['reference_max_z']+[actual['max_z']]));assert error<1e-11;maxerr=max(maxerr,error)
  # Column and reference-row permutation cannot change this candidate's rank.
  order=list(range(len(tails)));rng.shuffle(order);permuted=C.compare([[row[j] for j in order] for row in rows[:-1]],[rows[-1][j] for j in order],[tails[j] for j in order]);assert permuted['family_rank']==rank
  shuffled=rows[:-1].copy();rng.shuffle(shuffled);assert C.compare(shuffled,rows[-1],tails)['family_rank']==rank
 assert C.compare(cases[1][0][:-1],cases[1][0][-1],cases[1][1])['family_rank_fraction']==1.
 assert C.compare(cases[-1][0][:-1],cases[-1][0][-1],cases[-1][1])['gate']
 # Exercise every possible marked row using integer data and duplicate ties.
 exchangeable=[[float(i%7),float((i*3)%11),float(i%2)] for i in range(25)];tails=['lower','upper','lower'];marked=0
 for i in range(len(exchangeable)):
  rows=exchangeable[:i]+exchangeable[i+1:]+[exchangeable[i]];expected=scalar(rows,tails)[1];assert C.compare(rows[:-1],rows[-1],tails)['family_rank']==expected;marked+=1
 n=928;fixtures=[[3]*n,[i%29 for i in range(n)],[rng.randrange(29) for _ in range(617)],[i*29//n for i in range(n)]];pvmax=0.;invariants=0
 for values in fixtures:
  native=list(P.score_provenance(np.array(values,dtype=np.int64)).values());expected=provenance_scalar(values,P.WIDTHS);err=max(abs(x-y) for x,y in zip(native,expected));assert err<1e-9;pvmax=max(pvmax,err)
  perm=list(range(29));rng.shuffle(perm);renamed=list(P.score_provenance(np.array([perm[x] for x in values],dtype=np.int64)).values());assert np.allclose(native,renamed,atol=1e-9,rtol=0);invariants+=1
  if len(values)%8==0:
   reverse=list(P.score_provenance(np.array(values[::-1],dtype=np.int64)).values());assert np.allclose(native,reverse,atol=1e-9,rtol=0);invariants+=1
 assert all(v==0. for v in P.score_provenance(np.arange(n)%29).values())
 r=dict(calibration_sha256=hashlib.sha256((a.producer_root/'calibration.py').read_bytes()).hexdigest(),provenance_sha256=hashlib.sha256((a.producer_root/'provenance.py').read_bytes()).hexdigest(),checker_sha256=hashlib.sha256((H/'check_calibration_provenance.py').read_bytes()).hexdigest(),family_scalar_matrix_cases=len(cases),marked_row_permutation_cases=marked,maximum_standardized_score_error=maxerr,exact_constant_columns_zero=True,inclusive_ties_retained=True,column_and_reference_permutation_ranks_verified=True,provenance_scalar_cases=len(fixtures),provenance_metrics_per_case=8,maximum_provenance_error=pvmax,symbol_relabel_and_reversal_invariants=invariants,balanced_cycle_all8metrics_zero=True,target_loaded_or_scored=False,interpretation='Symmetric maxZ rank is conditionally exchangeable under the fixed generator; synthetic tests do not validate generator identity, incompressibility, OTP or every alternative.')
 a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
