"""Independent post-control diagnosis; no manuscript loading or scoring."""
import argparse,ast,hashlib,importlib.util,json,math,random,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np

def encoder(plain,key,sign,seed):
    rng=random.Random(seed);cipher=[];skips=[];used=[];pointer=0
    for p in plain:
        rejected=0
        while True:
            candidate=(p-sign*key[pointer])%29
            if cipher and candidate==cipher[-1] and rng.random()<.83:
                pointer+=1;rejected+=1;continue
            break
        cipher.append(candidate);skips.append(rejected);used.append(pointer);pointer+=1
    return cipher,skips,used

def feasible(cipher,plain,key,sign,phase):
    if len(cipher)!=len(plain) or (cipher[0]+sign*key[phase])%29!=plain[0]:return False
    states={phase}
    for i in range(1,len(cipher)):
        after=set()
        for previous in states:
            for delta in range(4):
                accepted=previous+1+delta
                if accepted>=len(key):break
                if (cipher[i]+sign*key[accepted])%29!=plain[i]:continue
                if all((plain[i]-sign*key[j])%29==cipher[i-1] for j in range(previous+1,accepted)):after.add(accepted)
        states=after
        if not states:return False
    return True

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--producer-root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();assert not a.output.exists();h=a.producer_root;start=time.perf_counter()
    read=lambda path:json.loads(path.read_bytes());sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    plan=read(h/'controls-plan-frozen.json');report=read(h/'controls-results.json')
    for name,digest in plan['pins'].items():assert sha(h/name)==digest,name
    assert report['plan_sha256']==sha(h/'controls-plan-frozen.json')
    spec=importlib.util.spec_from_file_location('keyword_control_audit_engine',h/'engine.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
    source=h/'source/liber-primus/analysis/campaign18_skip/sweep.py';node=next(n for n in ast.parse(source.read_text(encoding='utf8')).body if isinstance(n,ast.FunctionDef) and n.name=='beam');code=ast.unparse(node);assert code.count('return list(best[3])')==1
    env=dict(e.env);exec(compile(code.replace('return list(best[3])','return beams'),'<source-terminal-return-only>','exec'),env);native=env['beam']
    table=e.gp.GEMATRIA;spelling={row[0]:row[2] for row in table};counts={};total=0
    for line in (h/'source/liber-primus/data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        word,count=line.split();counts[word]=int(count);total+=int(count)
    logtotal=math.log10(total);model={word:math.log10(count)-logtotal for word,count in counts.items()};floor=math.log10(.01)-logtotal
    def score(plain):
        text=''.join(spelling[int(x)] for x in plain)
        if len(text)<4:return -999.
        total_score=0.
        for i in range(len(text)-3):total_score+=model.get(text[i:i+4],floor)
        return total_score/(len(text)-3)
    readings={row['id']:sum([p['rune_indices'] for p in row['decoded_pages']],[]) for row in read(h/'known-readings.json')['controls'] if row['id'] in ('warning','lp2-56')}
    summary={};diagnoses=[];maxerror=0.;over3=0;zero=0;native_beams=0;rows=report['controls']
    assert len(rows)==665 and sum(row['group']=='domain' for row in rows)==617
    for index,row in enumerate(rows):
        truth=readings[row['reading']];key=e.env['tile_key'](row['key'],4*len(truth)+64).tolist();cipher,skips,used=encoder(truth,key[row['phase']:],row['sign'],row['seed'])
        assert skips==row['skips'] and used==row['used'];actual_max=max(skips[1:],default=0);assert row['truth_encoder_path_max3']==(actual_max<=3);over3+=actual_max>3;zero+=sum(skips)==0
        phase=max(range(len(row['phase_scores'])),key=lambda i:row['phase_scores'][i]);assert row['best_screen'][1][-1]==phase and row['best_screen'][0]==row['phase_scores'][phase] and row['screen_gate']==(row['phase_scores'][phase]>-6)
        assert len(row['phase_scores'])==len(row['key']) and bool(row['full'])==row['screen_gate']
        if row['full']:
            full=row['full'][0];assert len(row['full'])==1 and full['offset']==phase and full['width']==500 and full['length']==len(truth)
            value=score(full['plain']);maxerror=max(maxerror,abs(value-full['score']));assert abs(value-full['score'])<1e-12
            assert feasible(cipher,full['plain'],key,row['sign'],phase)
            assert row['full_gate']==(value> -5.5) and row['hits']==int(row['full_gate']) and row['exact_recovery']==(full['plain']==truth)
            assert row['recovery_fraction']==sum(x==y for x,y in zip(full['plain'],truth))/len(truth)
            assert abs(score(full['best_normalized_terminal'])-full['best_normalized_terminal_score'])<1e-12
        if not row['exact_recovery']:
            # Every failed control: exact native full terminal list plus every native phase screen.
            ct=np.asarray(cipher,np.int64);k=np.asarray(key,np.int64)
            terminals=native(ct,k,row['sign'],phase,len(truth),500);native_beams+=1
            assert tuple(row['full'][0]['plain'])==terminals[0][3]
            ranks=[i+1 for i,t in enumerate(terminals) if list(t[3])==truth]
            full=row['full'][0];assert bool(ranks)==full['truth_in_terminal'] and (ranks[0] if ranks else None)==full['truth_first_cumulative_rank']
            phase_scores=[]
            for o in range(len(row['key'])):
                terminal=native(ct,k,row['sign'],o,min(90,len(truth)),300);native_beams+=1;phase_scores.append(score(terminal[0][3]))
            assert phase_scores==row['phase_scores']
            true_terminals=native(ct,k,row['sign'],row['phase'],len(truth),500);native_beams+=1
            truth_ranks=[i+1 for i,t in enumerate(true_terminals) if list(t[3])==truth]
            classification='retained-truth-outscored' if ranks else 'wrong-phase-selection' if phase!=row['phase'] else 'truth-not-retained'
            summary[classification]=summary.get(classification,0)+1
            diagnoses.append(dict(group=row['group'],keyword=row['keyword'],true_phase=row['phase'],selected_phase=phase,classification=classification,selected_truth_first_rank=ranks[0] if ranks else None,true_phase_truth_first_rank=truth_ranks[0] if truth_ranks else None,true_plaintext_admissible=feasible(cipher,truth,key,row['sign'],row['phase']),winner_score=score(terminals[0][3]),truth_score=score(truth),winner_cumulative=terminals[0][0],truth_cumulative=next((t[0] for t in true_terminals if list(t[3])==truth),None)))
    assert sum(row['screen_gate'] for row in rows if row['group']=='domain')==report['domain_screen_passes']==617
    assert sum(row['full_gate'] for row in rows if row['group']=='domain')==report['domain_full_passes']==617
    assert sum(row['exact_recovery'] for row in rows if row['group']=='domain')==report['domain_exact_recoveries']==575
    grids=[]
    for row in report['full_grids']:
        truth=readings[row['reading']];word=e.encode(row['true_keyword']);key=e.env['tile_key'](word,4*len(truth)+64).tolist();cipher,_,_=encoder(truth,key,-1,row['seed'])
        assert row['screens']==11256 and row['exact_output_found']==any(x['plain']==truth for x in row['full_outputs'])
        assert row['exact_gate_hit']==any(x['plain']==truth and score(x['plain'])> -5.5 for x in row['full_outputs'])
        for full in row['full_outputs']:assert abs(score(full['plain'])-full['score'])<1e-12
        own=[]
        for phase in range(len(word)):
            terminals=native(np.asarray(cipher,np.int64),np.asarray(key,np.int64),-1,phase,min(90,len(truth)),300);native_beams+=1;own.append(score(terminals[0][3]))
        selected=max(range(len(word)),key=lambda i:own[i]);assert row['best_screen'][1]==[row['true_keyword'],-1,False,selected] and row['best_screen'][0]==own[selected]
        grids.append(dict(reading=row['reading'],keyword=row['true_keyword'],own_key_all_phase_native_scores_verified=True,selected_phase=selected,exact_output_found=row['exact_output_found']))
    out=dict(status='PASS',controls_plan_sha256=sha(h/'controls-plan-frozen.json'),controls_results_sha256=sha(h/'controls-results.json'),audit_script_sha256=sha(Path(__file__)),all665_encodings_skip_paths_and_selected_output_admissibility_verified=True,all_saved_full_winner_and_normalized_witness_scores_verified=True,maximum_independent_normalized_score_error=maxerror,encoder_paths_over_max3=over3,zero_skip_plants=zero,failed_controls_native_diagnoses=diagnoses,failure_classification=summary,native_synthetic_beam_calls=native_beams,full_grid_true_keyword_phase_checks=grids,full_global_grids_independently_rerun=False,domain_gate_passes=617,domain_exact_recoveries=575,manuscript_loaded_or_scored=False,limits='Control-output audit after observing the synthetic receipt. Complete raw encoder/output checks; exact native beams for every failed control and true-key phases in four complete-grid controls, not a second complete wrong-key grid. Historical score-enumeration only if root authorizes a pretarget purpose amendment; no all-key or cipher-family rejection.',seconds=time.perf_counter()-start)
    a.output.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps({k:v for k,v in out.items() if k!='failed_controls_native_diagnoses'},indent=2))

if __name__=='__main__':main()
