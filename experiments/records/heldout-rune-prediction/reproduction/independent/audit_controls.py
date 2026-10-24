"""Independent reconstruction of every synthetic stream/rank and all18 planted CV profiles."""
import sys,json,argparse,random,math,hashlib,time,lzma
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
import oracle as O
from check_calibration_provenance import scalar,provenance_scalar
H=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def plant(kind,n,seed,lengths):
 rng=random.Random(seed);out=[]
 if kind=='balanced-bags':
  while len(out)<n:
   values=list(range(29));rng.shuffle(values);out+=values
  return out[:n]
 if kind=='frequency-drift':return [rng.randrange(14)+(15 if i>=n//2 else 0) for i in range(n)]
 if kind=='permuted-order2':
  values=plant('order2',n,seed,lengths);rng.shuffle(values)
  for value in values:
   if out and value==out[-1] and rng.random()<.83:value=rng.randrange(29)
   out.append(value)
  return out
 if kind=='fold-mismatch':
  for j,size in enumerate(lengths):
   page=[]
   for i in range(size):
    if i==0:value=rng.randrange(29)
    elif rng.randrange(29)==0:value=page[-1]
    else:value=(page[-1]+(1 if j%2==0 else 2))%29
    if page and value==page[-1] and rng.random()<.83:value=rng.randrange(29)
    page.append(value)
   out+=page
  return out
 for i in range(n):
  if kind=='order1':
   if i==0:value=rng.randrange(29)
   elif rng.randrange(29)==0:value=out[-1]
   else:value=(out[-1]+1)%29
  elif kind=='order2':value=rng.randrange(29) if i<2 or rng.random()<.1 else (out[-2]+out[-1]+1)%29
  else:raise ValueError(kind)
  if out and value==out[-1] and rng.random()<.83:value=rng.randrange(29)
  out.append(value)
 return out

def cv(values,lengths):
 pages=[];start=0
 for size in lengths:pages.append(values[start:start+size]);start+=size
 total=np.zeros(16);folds=[]
 for fold in (0,1):
  train=[p for j,p in enumerate(pages) if j%2!=fold];test=[p for j,p in enumerate(pages) if j%2==fold];model=O.fit(train,8);sums=[];positions=None
  for kind in ['kt','ppm']:
   for k in range(1,9):
    row=O.score(test,model,kind,k,8);sums.append(row['total_bits']);positions=row['positions']
  total+=sums;folds.append(dict(scored_positions=positions,loss_sums=sums))
 n=sum(f['scored_positions'] for f in folds)
 return total/n,folds

def main():
 p=argparse.ArgumentParser();p.add_argument('--producer-root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();assert not a.output.exists();root=a.producer_root;plan=read(root/'controls-plan-frozen.json');protocol=read(root/'protocol-frozen.json');result=read(root/'controls-results.json');started=time.perf_counter()
 for path,digest in protocol['pins'].items():assert sha(root/path)==digest,path
 assert result['plan_sha256']==sha(root/'controls-plan-frozen.json')==protocol['controls_plan_sha256']
 assert result['tails']==['lower']*23+['upper']*3 and len(result['names'])==26
 lengths=plan['lengths'];n=sum(lengths);streams={};generator_checks=0
 for group,count,key in [('reference',199,'reference_seed_start'),('negative_validation',99,'validation_seed_start')]:
  assert len(result[group])==count
  for j,row in enumerate(result[group]):
   seed=plan[key]+j;assert row['seed']==seed;values=O.filtered(random.Random(seed),n);assert hashlib.sha256(bytes(values)).hexdigest()==row['stream_sha256'];assert sum(x==y for x,y in zip(values,values[1:]))==row['adjacent_repeats'];generator_checks+=1
 for row in result['positive']:
  values=plant(row['kind'],n,row['seed'],lengths);assert hashlib.sha256(bytes(values)).hexdigest()==row['stream_sha256'];assert sum(x==y for x,y in zip(values,values[1:]))==row['adjacent_repeats'];streams[(row['kind'],row['seed'])]=values;generator_checks+=1
 assert len(result['positive'])==18
 refs=[row['values'] for row in result['reference']];rank_checks=0;zerror=0.
 for row in result['negative_validation']+result['positive']:
  expected,rank,constants=scalar(refs+[row['values']],result['tails']);reported=row['comparison'];assert rank==reported['family_rank'] and rank/200==reported['family_rank_fraction'];assert constants==reported['constant_metrics'];error=max(abs(x-y) for x,y in zip(expected,reported['reference_max_z']+[reported['max_z']]));assert error<1e-8;zerror=max(zerror,error)
  marginal=[]
  for j,tail in enumerate(result['tails']):
   direction=-1 if tail=='lower' else 1;values=sorted(r[j]*direction for r in refs);at=.99*(len(values)-1);lo=math.floor(at);hi=math.ceil(at);threshold=values[lo]*(hi-at)+values[hi]*(at-lo) if hi!=lo else values[lo];marginal.append(row['values'][j]*direction>threshold)
  assert marginal==reported['marginal_strict_1percent_flags'] and reported['gate']==(rank/200<.01 and any(marginal));rank_checks+=1
 maxrate=0.;maxsum=0.;profiles=[];compress_checks=0
 for row in result['positive']:
  values=streams[(row['kind'],row['seed'])];rates,folds=cv(values,lengths);error=float(np.max(np.abs(rates-np.array(row['context']['bits_per_rune']))));assert error<1e-10;maxrate=max(maxrate,error)
  for actual,expected in zip(row['context']['folds'],folds):
   assert actual['scored_positions']==expected['scored_positions'];error=float(np.max(np.abs(np.array(actual['loss_sums'])-expected['loss_sums'])));assert error<1e-6;maxsum=max(maxsum,error)
  integer=0
  for x in values:integer=integer*29+x
  packed=integer.to_bytes((integer.bit_length()+7)//8,'big')
  for mode,data in [('raw1',bytes(values)),('packed',packed)]:
   compressed=len(lzma.compress(data,preset=9|lzma.PRESET_EXTREME));assert compressed==row['compression'][mode]['compressed_bytes'] and len(data)==row['compression'][mode]['input_bytes'];assert row['compression'][mode]['bits_per_rune']==8*compressed/n;compress_checks+=1
  profiles.append(dict(kind=row['kind'],seed=row['seed'],maximum_bits_per_rune_error=float(np.max(np.abs(rates-np.array(row['context']['bits_per_rune'])))),all16_profiles_verified=True))
  print('Audited plant',row['kind'],row['seed'],flush=True)
 assert sum(r['comparison']['gate'] for r in result['negative_validation'])==result['negative_family_gate_passes']
 for kind,count in result['plant_family_passes'].items():assert count==sum(r['comparison']['gate'] for r in result['positive'] if r['kind']==kind)
 receipt=dict(protocol_sha256=sha(root/'protocol-frozen.json'),controls_results_sha256=sha(root/'controls-results.json'),audit_script_sha256=sha(H/'audit_controls.py'),oracle_sha256=sha(H/'oracle.py'),generated_stream_hashes_checked=generator_checks,independent_family_comparisons_checked=rank_checks,maximum_standardized_score_error=zerror,standardized_numeric_note='Scalar fsum versus vector mean gives up to2.13e-9 Z difference: an8.88e-15 mean difference at KT6 SD4.17e-6. Every inclusive family rank/gate agrees exactly; original1e-10 toy tolerance was too strict for this normalization. No scientific threshold changed.',full_planted_predictive_profiles_checked=len(profiles),models_per_profile=16,maximum_bits_per_rune_error=maxrate,maximum_fold_loss_sum_error=maxsum,lzma_source_mode_checks=compress_checks,profiles=profiles,negative_joint_flags=result['negative_family_gate_passes'],plant_family_passes=result['plant_family_passes'],limits='Synthetic only.199reference gate differs from final1000bank; unchanged controls must be rechecked against finalbank before target. PackedLZMA weak power retained. No OTP/family/randomness verdict.',seconds=time.perf_counter()-started)
 a.output.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in receipt.items() if k!='profiles'},indent=2))
if __name__=='__main__':main()
