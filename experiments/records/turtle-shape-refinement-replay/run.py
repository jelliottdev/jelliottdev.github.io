"""Replay six fixed source refinements using four shared 2000-shuffle walk series."""
import argparse,ast,hashlib,importlib.util,json,math,random,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PLAN=json.loads((HERE/'plan.json').read_bytes())
for r in PLAN['inputs']:assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']

def defs(name,names,env):
 tree=ast.parse((HERE/name).read_text(encoding='utf8'));nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),name,'exec'),env);return env
ENV={'np':np,'math':math,'random':random,'RASTER':128,'sqrt':math.sqrt,'erf':math.erf}
defs('source-turtle_engine.py',['walk','rasterize','_ccw_v','_seg_intersections_sampled','_components','_iou','_symmetry','detect','two_sided_p'],ENV)
defs('source-lib_numchannel.py',['shuffled'],ENV)
defs('source-sweep.py',['_z_tail_p','erfc_two_sided','math_erfc'],ENV)
defs('source-phase0_control.py',['planted_square','planted_blockword'],ENV)
STATS=['closure','self_intersections','bbox_fill','caging','symmetry','components']
spec=importlib.util.spec_from_file_location('independent_turtle',ROOT/'experiments/records/lp2-turtle-spatial-replay/run.py');ind=importlib.util.module_from_spec(spec);spec.loader.exec_module(ind)
index=json.loads((ROOT/'data/index.json').read_bytes());alphabet=index['alphabet'];lookup={r['rune']:i for i,r in enumerate(alphabet)};primes=[r['prime'] for r in alphabet]
pages=[f'lp2-{i:02d}' for i in list(range(50))+list(range(51,56))];runes=''.join(c for pid in pages for c in (ROOT/f'text/{pid}.txt').read_text(encoding='utf8') if c in lookup)
assert len(runes)==12956 and hashlib.sha256(runes.encode('utf8')).hexdigest()==PLAN['stream_pin']['sha256_utf8_runes'];idx=[lookup[r] for r in runes];streams={'value':[primes[i] for i in idx],'pi':[i+1 for i in idx]}
groups={r['combo']:{k:r[k] for k in ['combo','stream','modulus','turn','step']} for r in PLAN['cases']};actual_hashes=set();walk_calls=0;ind_checks=0

def trajectory(values,group,seed,independent=False):
 global walk_calls,ind_checks
 x,y=ENV['walk'](values,group['modulus'],group['turn'],group['step']);d=ENV['detect'](x,y,rng_seed=seed);walk_calls+=1;actual_hashes.add(hashlib.sha256(x.tobytes()+y.tobytes()).hexdigest())
 if independent:
  ix,iy=ind.walk(values,group['modulus'],group['turn'],group['step']);assert np.array_equal(x,ix) and np.array_equal(y,iy)
  assert np.array_equal(ENV['rasterize'](x,y),ind.raster(ix,iy));other=ind.measure(ix,iy,seed)
  for s in ['bbox_fill','symmetry','components']:assert d[s]==other[s],(group['combo'],s,d[s],other[s])
  ind_checks+=1
 return d

def controls():
 out={}
 for name,values in [('square',ENV['planted_square']()),('blockcomb',ENV['planted_blockword']())]:
  g={'combo':'control_'+name,'modulus':4,'turn':'absolute','step':'unit'};real=trajectory(values,g,3301,True);samples={s:[] for s in STATS}
  for k in range(200):
   result=trajectory(ENV['shuffled'](values,3301+k),g,3301+k,k<2)
   for s in STATS:samples[s].append(float(result[s]))
  ps={s:float(ENV['two_sided_p'](real[s],samples[s])) for s in STATS};fired=[s for s,p in ps.items() if p<.01];assert len(fired)>=2
  out[name]={'runes':len(values),'real':real,'empirical_p':ps,'fired_stats':fired,'phase0_rule_pass':len(fired)>=2,'null_walks':200}
 return out

p=argparse.ArgumentParser();p.add_argument('--benchmark',action='store_true');args=p.parse_args()
if args.benchmark:
 n=10;start=time.perf_counter()
 for g in groups.values():
  values=streams[g['stream']]
  for k in range(n):trajectory(ENV['shuffled'](values,103301+k),g,103301+k,k==0)
 seconds=time.perf_counter()-start;r={'four_combo_null_walks':len(groups)*n,'elapsed_seconds':seconds,'estimated_8000_null_walk_seconds':seconds*200,'source_detect_all6_stats':True,'independent_walk_raster_selected_stat_checks':ind_checks};(HERE/'benchmark.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print(json.dumps(r,indent=2))
else:
 control=controls();samples={};reals={}
 for combo,g in groups.items():
  values=streams[g['stream']];reals[combo]=trajectory(values,g,3301,True);samples[combo]={s:[] for s in STATS}
  for k in range(2000):
   result=trajectory(ENV['shuffled'](values,103301+k),g,103301+k,k<PLAN['controls']['independent_walk_checks_per_combo'])
   for s in STATS:samples[combo][s].append(float(result[s]))
  print('Completed shared refinement series:',combo,flush=True)
 rows=[]
 for case in PLAN['cases']:
  combo,stat=case['combo'],case['stat'];real=float(reals[combo][stat]);arr=np.asarray(samples[combo][stat]);lo=int(np.count_nonzero(arr<=real));hi=int(np.count_nonzero(arr>=real));emp=float(ENV['two_sided_p'](real,arr));tail=float(ENV['_z_tail_p'](real,arr));flag=emp==0.0 and tail<PLAN['bonferroni_bar']
  archived=case['source_saved_refinement'];rows.append({'combo':combo,'stat':stat,'real':real,'samples':2000,'count_le_real':lo,'count_ge_real':hi,'sample_mean':float(arr.mean()),'sample_sd_ddof1':float(arr.std(ddof=1)),'source_empirical_p':emp,'source_gaussian_tail_p':tail,'source_flag_rule_pass':flag,'archived_empirical_p':archived['emp_p'],'archived_gaussian_tail_p':archived['z_tail_p'],'empirical_difference':emp-archived['emp_p'],'gaussian_tail_difference':tail-archived['z_tail_p']})
 (HERE/'null-samples.json').write_text(json.dumps(samples,separators=(',',':'))+'\n',encoding='utf8')
 r={'schema':'turtle-six-refinement-replay-v1','plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),'stream_runes':len(runes),'stream_sha256':hashlib.sha256(runes.encode('utf8')).hexdigest(),'selected_statistics':6,'distinct_combo_series':len(groups),'refinement_surrogate_walk_evaluations':8000,'refinement_real_walk_evaluations':4,'control_walk_evaluations':402,'total_walk_evaluations':walk_calls,'actual_unique_coordinate_digest_count':len(actual_hashes),'independent_walk_raster_selected_stat_checks':ind_checks,'source_scalar_refine_equivalent_walk_calls':12000,'saved_all6_stats_per_shared_walk':True,'rows':rows,'flagged_count':sum(x['source_flag_rule_pass'] for x in rows),'source_bonferroni_bar':PLAN['bonferroni_bar'],'phase0_controls':control,'null_samples_sha256':hashlib.sha256((HERE/'null-samples.json').read_bytes()).hexdigest(),'limits':'Shared series are not independent tests; empirical zero is a finite-sample floor. Gaussian extrapolation is model-based, especially fragile for discrete raster counts. No decryption or whole-family power claim.'}
 (HERE/'results.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print(json.dumps({'selected_statistics':6,'distinct_series':len(groups),'actual_unique_coordinate_digests':len(actual_hashes),'flagged':r['flagged_count'],'rows':rows},indent=2))
