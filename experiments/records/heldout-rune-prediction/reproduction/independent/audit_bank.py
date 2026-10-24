"""Independent synthetic final-bank audit; complete identities/ranks and fixed raw-metric sample."""
import sys,json,argparse,random,math,hashlib,time,lzma
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
import oracle as O
from audit_controls import cv
from check_calibration_provenance import scalar,provenance_scalar
H=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--producer-root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();assert not a.output.exists();root=a.producer_root;started=time.perf_counter()
 plan=read(root/'bank-plan-frozen.json');protocol=read(root/'protocol-frozen.json');report=read(root/'null-bank/receipt.json');controls=read(root/'controls-results.json');ap=read(H/'bank-audit-plan.json')
 for row in ap['files']:assert sha(H/row['path'])==row['sha256']
 for path,digest in plan['pins'].items():assert sha(root/path)==digest,path
 assert report['bank_plan_sha256']==sha(root/'bank-plan-frozen.json') and report['protocol_sha256']==sha(root/'protocol-frozen.json')==plan['protocol_sha256']
 assert report['synthetic_controls_sha256']==sha(root/'controls-results.json') and report['measurements_sha256']==sha(root/'null-bank/measurements.npz')
 arrays=np.load(root/'null-bank/measurements.npz',allow_pickle=False);metrics=arrays['metrics'];pages=arrays['page_loss_sums'];folds=arrays['fold_loss_sums'];assert metrics.shape==(1000,26) and pages.shape==(1000,55,16) and folds.shape==(1000,2,16)
 assert np.isfinite(metrics).all() and np.isfinite(pages).all() and np.isfinite(folds).all()
 lengths=[r['length'] for r in read(root/'input-shape.json')['pages']];n=sum(lengths);positions=sum(max(0,x-8) for x in lengths);assert n==12956 and positions==12516
 aggregate_error=float(np.max(np.abs(pages.sum(axis=1)/positions-metrics[:,:16])));assert aggregate_error<1e-10
 fold_error=max(float(np.max(np.abs(pages[:,parity::2].sum(axis=1)-folds[:,parity]))) for parity in (0,1));assert fold_error<1e-6
 concat=hashlib.sha256();selected={};repeat_counts=[]
 assert report['replicates']==len(report['rows'])==1000
 for i,row in enumerate(report['rows']):
  seed=3301241024000+i;assert row['replicate']==i and row['seed']==seed
  values=O.filtered(random.Random(seed),n);raw=bytes(values);concat.update(raw);assert hashlib.sha256(raw).hexdigest()==row['stream_sha256']
  repeats=sum(x==y for x,y in zip(values,values[1:]));assert repeats==row['adjacent_repeats'];repeat_counts.append(repeats)
  assert [values.count(x) for x in range(29)]==row['monograms']
  for j,mode in enumerate(['raw1','packed']):assert metrics[i,16+j]==row['compression'][mode]['bits_per_rune']==8*row['compression'][mode]['compressed_bytes']/n
  if i in ap['bank_full_profile_indices']:selected[i]=values
 assert concat.hexdigest()==report['concatenated_generated_streams_sha256']
 full_errors=[]
 for i,values in selected.items():
  rates,scalar_folds=cv(values,lengths);rate_error=float(np.max(np.abs(rates-metrics[i,:16])));assert rate_error<1e-10
  for f in range(2):assert np.max(np.abs(np.array(scalar_folds[f]['loss_sums'])-folds[i,f]))<1e-6
  integer=0
  for x in values:integer=integer*29+x
  packed=integer.to_bytes((integer.bit_length()+7)//8,'big')
  for j,(mode,data) in enumerate([('raw1',bytes(values)),('packed',packed)]):assert len(lzma.compress(data,preset=9|lzma.PRESET_EXTREME))==report['rows'][i]['compression'][mode]['compressed_bytes']
  pv=provenance_scalar(values,(29,58,116,232,464));pv_error=float(np.max(np.abs(np.array(pv)-metrics[i,18:])));assert pv_error<1e-8
  full_errors.append(dict(replicate=i,all26metrics_checked=True,maximum_predictive_rate_error=rate_error,maximum_provenance_error=pv_error));print('Independent full26metric bank row',i,'checked',flush=True)
 lookup={(group,row.get('kind','filtered-validation'),row['seed']):row for group in ['negative_validation','positive'] for row in controls[group]};rank_checks=0;maxz=0.
 refs=metrics.tolist();tails=report['tails'];assert tails==['lower']*23+['upper']*3 and report['names']==controls['names']
 for row in report['unchanged_synthetic_recomparisons']:
  original=lookup[(row['group'],row['kind'],row['seed'])];assert row['stream_sha256']==original['stream_sha256'];values=original['values'];scores,rank,constants=scalar(refs+[values],tails);cmp=row['comparison'];assert rank==cmp['family_rank'] and rank/1001==cmp['family_rank_fraction'] and cmp['constant_metrics']==constants
  error=max(abs(x-y) for x,y in zip(scores,cmp['reference_max_z']+[cmp['max_z']]));assert error<ap['numeric_allowance']['standardized_scalar_vector_z'];maxz=max(maxz,error)
  marginal_ranks=[];flags=[]
  for j,tail in enumerate(tails):
   direction=-1 if tail=='lower' else 1;column=sorted(r[j]*direction for r in refs);value=values[j]*direction;marginal_ranks.append(1+sum(v>=value for v in column));at=.99*999;lo=math.floor(at);fraction=at-lo;threshold=column[lo]+fraction*(column[lo+1]-column[lo]);flags.append(value>threshold)
  assert marginal_ranks==cmp['marginal_rank'] and flags==cmp['marginal_strict_1percent_flags'] and cmp['gate']==(rank/1001<.01 and any(flags));rank_checks+=1
 assert rank_checks==117
 assert report['negative_joint_flags']==sum(r['comparison']['gate'] for r in report['unchanged_synthetic_recomparisons'] if r['group']=='negative_validation')
 for kind,count in report['positive_joint_flags_by_kind'].items():assert count==sum(r['comparison']['gate'] for r in report['unchanged_synthetic_recomparisons'] if r['kind']==kind)
 addendum=read(root/'reporting-addendum-frozen.json');assert addendum['protocol_sha256']==sha(root/'protocol-frozen.json') and addendum['controls_results_sha256']==sha(root/'controls-results.json') and addendum['uniform_bits_per_rune']==math.log2(29)
 assert not (root/'target-results.json').exists() and not (root/'target').exists()
 result=dict(protocol_sha256=sha(root/'protocol-frozen.json'),bank_plan_sha256=sha(root/'bank-plan-frozen.json'),bank_receipt_sha256=sha(root/'null-bank/receipt.json'),audit_plan_sha256=sha(H/'bank-audit-plan.json'),audit_script_sha256=sha(H/'audit_bank.py'),all_generated_streams_checked=1000,all_stream_hashes_repeats_monograms_and_aggregate_hash_verified=True,all1000page_fold_rate_identities_verified=True,maximum_page_rate_identity_error=aggregate_error,maximum_page_fold_sum_error=fold_error,fixed_full_metric_profiles_checked=full_errors,unchanged_plant_negative_recomparisons_verified=rank_checks,maximum_standardized_scalar_vector_error=maxz,negative_joint_flags=report['negative_joint_flags'],plant_family_passes=report['positive_joint_flags_by_kind'],packed_lzma_reference_constant=bool(np.all(metrics[:,17]==metrics[0,17])),packed_lzma_reference_value=float(metrics[0,17]),uniform_baseline_reporting_addendum_verified=True,repeat_range=[min(repeat_counts),max(repeat_counts)],pretarget_review='PASS for fixed conditional comparison; all mandatory arms/control outcomes retained. Source uniformity/repeats matched only in expectation; no general cipher/OTP claim. Root explicit target authorization still required.',coverage='Complete generator/hash/aggregation and all117calibrations; independently recomputed raw26metrics at3fixed bank rows, not every bank metric.',target_loaded_or_scored=False,seconds=time.perf_counter()-started)
 a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
