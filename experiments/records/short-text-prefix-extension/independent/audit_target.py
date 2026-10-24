"""Portable exhaustive integer audit of the newly eligible short-prefix alignments."""
import sys,json,argparse,time
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
import direct as D
H=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_bytes())

def audit(root,output,inputs,baseline=None):
    started=time.perf_counter();p=read(root/'protocol-frozen.json');result=read(output/'results.json');plan=read(H/'audit-plan-frozen.json');pre=read(H/'preflight-v3-receipt.json');review=read(H/'protocol-review.json')
    for row in plan['files']:assert D.sha((H/row['path']).read_bytes())==row['sha256']
    for path,digest in p['pins'].items():assert D.sha((root/path).read_bytes())==digest,path
    assert result['protocol_sha256']==review['protocol_sha256']==D.sha((root/'protocol-frozen.json').read_bytes())
    assert D.sha((root/'inputs-frozen.json').read_bytes())==pre['baseline_manifest_sha256']
    manifest=read(root/'inputs-frozen.json');corpus={}
    for row in manifest['corpus']:
        if row['words']>=2928:continue
        raw=(inputs/row['path']).read_bytes();assert D.sha(raw)==row['sha256'] and len(raw)==row['bytes']
        values=D.normalize(raw,row['path']);assert len(values)==row['words'] and D.ah(values)==row['lengths_sha256'];corpus[row['name']]=values
    m=manifest['manuscript'];raw=(inputs/m['path']).read_bytes();assert D.sha(raw)==m['sha256']
    obs,fc=D.manuscript(raw,root/'source/liber-primus/src/lp/gematria.py');assert D.ah(obs)==m['lengths_sha256'] and D.ah(fc)==m['fcounts_sha256'];patterns=D.patterns(obs,fc)
    assert p['patterns']=={n:dict(width=len(o),observed_sha256=D.ah(o),fcounts_sha256=D.ah(f)) for n,(o,f) in patterns.items()}
    archive=output/'alignment-scores.npz';assert D.sha(archive.read_bytes())==result['score_arrays_sha256']
    saved=np.load(archive,allow_pickle=False);expected_keys=set();checked=0;maximum_error=0.;winners=[];rowindex=0;global_rows=[];full_real=0;different_integer_first=0
    for gi,w in enumerate((400,120)):
        texts=sorted(n for n,a in corpus.items() if len(a)>=w);pats=[(n,v) for n,v in patterns.items() if len(v[0])==w]
        assert [r['name'] for r in p['selected'][str(w)]]==texts
        group=result['groups'][gi];assert group['width']==w
        global_best={n:dict(count=-1.,text=None,offset=-1) for n,_ in pats}
        for ti,text in enumerate(texts):
            values=corpus[text]
            for pi,(name,(o,f)) in enumerate(pats):
                key=f'w{w}_t{ti}_p{pi}';expected_keys.update([key+'_fft',key+'_integer']);raw_scores=saved[key+'_fft'];stored_int=saved[key+'_integer'];integer=D.count(values,o,f)
                assert len(integer)==len(values)-w+1==len(raw_scores) and raw_scores.dtype==np.dtype('float64')
                assert np.array_equal(stored_int,integer);error=float(np.max(np.abs(raw_scores-integer)));assert error<plan['fft_numerical_policy']['maximum_absolute_count_error']
                j=int(np.argmax(raw_scores));best=int(integer.max());ties=np.flatnonzero(integer==best).tolist();assert j in ties
                r=result['per_text_winners'][rowindex];rowindex+=1
                assert (r['key'],r['pattern'],r['text'],r['words'],r['starts'],r['offset'])==(key,name,text,len(values),len(integer),j)
                assert r['raw_max']==float(raw_scores[j])==group['per_text'][name][text]
                assert r['integer_max']==r['selected_integer']==best and r['integer_ties']==ties and r['complete']==(best==w)
                assert abs(r['max_fft_error']-error)<1e-12
                if r['raw_max']>global_best[name]['count']:global_best[name]=dict(count=r['raw_max'],text=text,offset=j)
                if name.startswith('real') and best==w:full_real+=1
                if j!=ties[0]:different_integer_first+=1
                checked+=len(integer);maximum_error=max(maximum_error,error)
                winners.append(dict(pattern=name,text=text,alignment_scores=len(integer),integer_max=best,source_raw_offset=j,earliest_integer_max_offset=ties[0],integer_tie_count=len(ties),max_fft_error=error,integer_scores_sha256=D.sha(integer.astype('<i8').tobytes())))
        assert group['best']==global_best
        for name in group['per_text']:assert set(group['per_text'][name])==set(texts)
        assert set(group['best'])=={n for n,_ in pats}
        global_rows.append(dict(width=w,best=global_best))
    assert set(saved.files)==expected_keys and rowindex==len(result['per_text_winners'])==54
    assert checked==result['alignment_scores']==p['alignment_scores']==40245 and result['complete_real_prefix_matches']==full_real
    supplement=read(root/'controls-summary-supplement.json')
    assert supplement['protocol_sha256']==result['protocol_sha256'] and supplement['controls_sha256']==D.sha((root/'controls.json').read_bytes())
    assert supplement['all37_max_fft_error']==review['maximum_all_case_fft_error'] and supplement['fixed_independent_tolerance']==.001
    context=None
    if baseline:
        bm=baseline/'reproduction/inputs-frozen.json';assert D.sha(bm.read_bytes())==D.sha((root/'inputs-frozen.json').read_bytes())
        for row in manifest['source_files']:
            assert D.sha((baseline/'reproduction/source'/row['path']).read_bytes())==D.sha((root/'source'/row['path']).read_bytes())==row['sha256']
        old=read(baseline/'reproduction/scan_results.json');old_rows={n:old['best'][n] for n in patterns}
        assert all(set(old['per_text'][n])=={r['name'] for r in manifest['corpus'] if r['words']>=2928} for n in patterns)
        # Same original parser bytes, manuscript array hashes, RNG and six pairs;
        # old source84 outputs remain reused evidence, not fresh short-target work.
        context=dict(old84_scope_verified=True,same_manifest_source_and_pattern_pairs=True,old_best_by_pattern=old_rows,merged_target_scan_performed=False,limits='Contextual comparison only: no original84 alignment arrays rescanned or combined into a new source run. Original six pattern hashes are reconstructed from identical pinned source/inputs/RNG, not an archived explicit pattern-hash table.')
    return dict(schema='c01-short-prefix-independent-target-audit-v1',protocol_sha256=result['protocol_sha256'],audit_plan_sha256=D.sha((H/'audit-plan-frozen.json').read_bytes()),direct_counter_sha256=D.sha((H/'direct.py').read_bytes()),audit_script_sha256=D.sha((H/'audit_target.py').read_bytes()),results_sha256=D.sha((output/'results.json').read_bytes()),score_arrays_sha256=D.sha(archive.read_bytes()),all_new_alignment_scores_checked=checked,per_text_pattern_rows_checked=rowindex,exact_inputs_verified=10,prefix_membership=dict(width400=8,width120=10),maximum_fft_integer_error=maximum_error,fixed_error_allowance=.001,source_winners_all_integer_maxima=True,source_raw_float_and_sorted_text_selections_verified=True,raw_selected_offset_differs_from_earliest_integer_maximum_rows=different_integer_first,complete_real_prefix_matches=full_real,global_winners=global_rows,winners=winners,prior_context=context,limits='Exhaustive integer audit of all new alignments. FFT raw selection retained; no rounding to choose. Counts are compatible positions, not decoded words; two fixed shuffles do not establish a global probability. No historical224corpus or original84 rescan.',seconds=time.perf_counter()-started)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-root',required=True,type=Path);p.add_argument('--result-root',required=True,type=Path);p.add_argument('--inputs-root',required=True,type=Path);p.add_argument('--baseline-root',type=Path);p.add_argument('--output',type=Path);p.add_argument('--check-only',action='store_true');a=p.parse_args();assert a.check_only != (a.output is not None),'Choose --check-only or --output NEW_FILE';assert a.output is None or not a.output.exists()
    r=audit(a.run_root.resolve(),a.result_root.resolve(),a.inputs_root.resolve(),a.baseline_root.resolve() if a.baseline_root else None)
    if a.output:a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ['winners','prior_context']},indent=2))
if __name__=='__main__':main()
