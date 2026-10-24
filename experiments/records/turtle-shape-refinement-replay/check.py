"""Independent tail/count/control arithmetic over every saved shared refinement sample."""
import hashlib,json,math,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
plan=json.loads((HERE/'plan.json').read_bytes());result=json.loads((HERE/'results.json').read_bytes());samples=json.loads((HERE/'null-samples.json').read_bytes())
for r in plan['inputs']:assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256']
assert result['plan_sha256']==hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()
assert result['null_samples_sha256']==hashlib.sha256((HERE/'null-samples.json').read_bytes()).hexdigest()
assert len(samples)==4 and all(len(values)==2000 for group in samples.values() for values in group.values())
flags=[];rows=[]
for r in result['rows']:
 data=samples[r['combo']][r['stat']];obs=r['real'];lo=sum(v<=obs for v in data);hi=sum(v>=obs for v in data);emp=2*min(lo,hi)/len(data)
 mean=statistics.fmean(data);sd=statistics.stdev(data);z=abs(obs-mean)/sd if sd else float('inf') if obs!=mean else 0;tail=math.erfc(z/math.sqrt(2))
 assert (lo,hi)==(r['count_le_real'],r['count_ge_real']) and emp==r['source_empirical_p']
 assert math.isclose(mean,r['sample_mean'],abs_tol=1e-12,rel_tol=1e-12) and math.isclose(sd,r['sample_sd_ddof1'],abs_tol=1e-12,rel_tol=1e-12)
 assert math.isclose(tail,r['source_gaussian_tail_p'],abs_tol=2e-14,rel_tol=1e-10)
 flag=emp==0 and tail<plan['bonferroni_bar'];assert flag==r['source_flag_rule_pass'];archived=next(c['source_saved_refinement'] for c in plan['cases'] if c['combo']==r['combo'] and c['stat']==r['stat']);assert emp==archived['emp_p'] and flag==bool(archived['clears_bonferroni']);flags.append(flag);rows.append({'combo':r['combo'],'stat':r['stat'],'count_le':lo,'count_ge':hi,'empirical':emp,'independent_erfc_tail':tail,'same_flag':True})
assert not any(flags) and result['flagged_count']==0
assert result['total_walk_evaluations']==8406 and result['distinct_combo_series']==4 and result['refinement_surrogate_walk_evaluations']==8000
for name,c in result['phase0_controls'].items():
 expected=[s for s,p in c['empirical_p'].items() if p<.01];assert c['fired_stats']==expected and len(expected)>=2 and c['phase0_rule_pass']
assert result['independent_walk_raster_selected_stat_checks']==30
out={'schema':'turtle-refinement-independent-check-v1','all_saved_tail_samples_recounted':12000,'unique_saved_null_walk_series':4,'shared_null_walks':8000,'all_tail_means_sds_and_flags_match':True,'all_six_archived_empirical_tails_and_flags_match':True,'source_1_minus_erf_vs_independent_erfc_checked':True,'independent_walk_raster_selected_stat_checks':result['independent_walk_raster_selected_stat_checks'],'source_phase0_gates_pass':True,'flagged':0,'rows':rows,'limitation':'Recounting source gates does not validate Gaussian tails or establish detector power for arbitrary shapes. Six statistics are not six independent walk series.'}
(HERE/'independent-check.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))
