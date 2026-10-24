import sys,copy,math,ast,random,json,hashlib,argparse
from pathlib import Path
from fractions import Fraction
sys.dont_write_bytecode=True
from oracle import fit,kt,ppm,score,filtered
H=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();assert not a.output.exists();source=a.source_root/'liber-primus/analysis/campaign11_pin_the_filter.py'
 tree=ast.parse(source.read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='soft_pad');namespace={'N':29};exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(source)+'#soft_pad-only','exec'),namespace)
 generator_cases=0
 for seed in [0,3301,3301241024000,3301241024999]:
  for n in [0,1,2,61,12956]:
   for suppression in [0.,.83,1.]:
    for nonzero in [False,True]:
     plain=[(i*7+3)%29 if nonzero else 0 for i in range(n)]
     namespace['rng']=random.Random(seed);expected=namespace['soft_pad'](plain,suppression);actual=filtered(random.Random(seed),n,suppression,plain)
     assert actual==expected;generator_cases+=1
 m=fit([[0,1],[0,2]],8);assert kt(m,[0],1,1)==Fraction(1,11)
 assert kt(m,[8],7,1)==Fraction(1,29)
 assert (1,) not in m and (1,2) not in m  # no cross-page training transitions
 before=copy.deepcopy(m);s=score([[0,1,0,1,0,1,0,1,0,1]],m,'kt',1);assert m==before and s['positions']==2
 for kind in ['kt','ppm']:
  one=score([[0,1,0,1,0,1,0,1,0,1]],m,kind,1)
  split=score([[0,1,0,1,0],[1,0,1,0,1]],m,kind,1);assert split['positions']==0 and one['positions']==2
  assert m==before
 # Analytic full-count exclusion, closed alphabet and unseen-context checks.
 assert ppm({():{0:2,1:1}},[],0,0)==Fraction(2,5)
 assert ppm({():{0:2,1:1}},[],2,0)==Fraction(2,135)
 assert ppm({():{x:1 for x in range(29)}},[],3,0)==Fraction(1,29)
 assert ppm({},[1,2],3,2)==Fraction(1,29)
 rng=random.Random(241024020);probability_vectors=0
 for trial in range(40):
  pages=[[rng.randrange(29) for _ in range(rng.randrange(1,25))] for _ in range(5)];model=fit(pages,8)
  for order in range(9):
   history=[rng.randrange(29) for _ in range(order)]
   assert sum(kt(model,history,x,order) for x in range(29))==1
   assert sum(ppm(model,history,x,order) for x in range(29))==1
   probability_vectors+=2
 r=dict(source_generator_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),oracle_sha256=hashlib.sha256((H/'oracle.py').read_bytes()).hexdigest(),test_sha256=hashlib.sha256((H/'test_oracle.py').read_bytes()).hexdigest(),exact_original_soft_pad_cases=generator_cases,kt_and_ppm_probability_vectors=probability_vectors,probability_sums_exact_rational=True,analytic_kt_and_ppm_checks=True,no_cross_page_context=True,no_test_count_updates=True,common_burnin_positions_checked=True,target_loaded_or_scored=False,definition='KT additivehalf over29 fixedsymbols. PPM-C full-count exclusion after highercontext symbols, escape distinct/(total+distinct), emptyeffectivecontext escapes1, allremainingobserved closes escape and normalizes counts. Frozen training counts, per-page reset, common test burnin8. Await producer exact agreement before target review.')
 a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print('PASS',generator_cases,'source generator cases;',probability_vectors,'exact probability vectors; no target data')
if __name__=='__main__':main()
