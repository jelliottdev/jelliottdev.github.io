"""Frozen known-message and finite-padding controls; never opens actual payloads."""
import ast,hashlib,json,time
from pathlib import Path
import native as n
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def observer():
    tree=ast.parse((n.LP/'analysis/campaign18_skip/skipdecode.py').read_text(encoding='utf8'));fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='beam_decode');fn.name='observe_beam'
    end=next(i for i,x in enumerate(fn.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='best' for t in x.targets))
    fn.body=fn.body[:end]+[ast.Return(value=ast.Tuple(elts=[ast.Name(id='beams',ctx=ast.Load()),ast.Name(id='Kx',ctx=ast.Load())],ctx=ast.Load()))]
    env=dict(n.env);exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'source-return-observer','exec'),env);return env['observe_beam']
observe=observer()
def feasibility(ct,plain,K,sign):
    if (ct[0]+sign*K[0])%29!=plain[0]:return False,0
    states={0};largest=1
    for i in range(1,len(ct)):
        nxt=set()
        for previous in states:
            for skipped in range(4):
                accepted=previous+1+skipped
                if accepted>=len(K):break
                if (ct[i]+sign*K[accepted])%29!=plain[i]:continue
                if all((plain[i]-sign*K[j])%29==ct[i-1] for j in range(previous+1,accepted)):nxt.add(accepted)
        states=nxt;largest=max(largest,len(states))
        if not states:return False,largest
    return True,largest
def inspect(ct,key,sign,truth=None):
    original=n.decode(ct,key,sign=sign,o=0,beam_w=300,max_skip=3);beams,K=observe(ct,key,sign=sign,o=0,beam_w=300,max_skip=3)
    assert K==n.padded(key,len(ct));best=beams[0]
    assert original==dict(score=n.Q.score_norm(best[2]),beam_score=best[0],plain_idx=best[3],ptr_end=best[1],translit=best[2])
    norms=[n.Q.score_norm(x[2]) for x in beams];ix=max(range(len(beams)),key=lambda i:norms[i]);ranks=[i+1 for i,x in enumerate(beams) if x[3]==truth] if truth is not None else []
    return original,dict(terminal_count=len(beams),terminal_ordered_sha256=hashlib.sha256(json.dumps(beams,separators=(',',':')).encode()).hexdigest(),truth_in_terminal=bool(ranks),truth_first_rank=ranks[0] if ranks else None,best_normalized_score=norms[ix],best_normalized_rank=ix+1,best_normalized_output=beams[ix][3],best_normalized_pointer=beams[ix][1],effective_key_length=len(K)),beams
def boundary(key,sign):
    K=n.padded(key,256);ct=[0];plain=[sign*K[0]%29];pointer=0;used=[0];rejected=[]
    for i in range(1,256):
        skip=1 if i<=180 else 0
        if skip:
            p=(ct[-1]+sign*K[pointer+1])%29;rejected.append(pointer+1)
        else:p=(7*i+3)%29
        pointer+=skip+1;plain.append(p);ct.append((p-sign*K[pointer])%29);used.append(pointer)
    assert pointer==435 and {355,356,357}<=set(used+rejected)
    assert feasibility(ct,plain,K,sign)[0]
    return ct,plain,used
def main():
    plan=json.loads((H/'controls-plan-frozen.json').read_bytes());execution=json.loads((H/'controls-execution-frozen.json').read_bytes())
    for p,h in {**plan['pins'],**execution['pins']}.items():assert sha(H/p)==h,p
    fixtures=json.loads((H/'control-fixtures-frozen.json').read_bytes())['fixtures'];keys=list(n.keys.items());rows=[];boundaries=[];started=time.perf_counter()
    for fixture in fixtures:
        plain=fixture['indices']
        for j,(label,key) in enumerate(keys):
            for sign in (-1,1):
                for atb in (0,1):
                    case=len(rows);seed=plan['positive_matrix']['seed_start']+case;row=dict(case=case,fixture=fixture['id'],key=label,sign=sign,atbash=atb,seed=seed)
                    try:
                        ct,skips,used=n.encrypt(plain,n.padded(key,len(plain)),sign=sign,supp=.83,seed=seed);actual=[28-x for x in ct] if atb else ct;decoded_ct=[28-x for x in actual] if atb else actual
                        original,terminal,_=inspect(decoded_ct,key,sign,plain);valid,statecount=feasibility(ct,plain,n.padded(key,len(ct)),sign);wrong_label,wrong_key=keys[(j+1)%len(keys)];wrong,wrong_terminal,_=inspect(decoded_ct,wrong_key,sign)
                        row.update(ciphertext=actual,skips=skips,used=used,source=original,terminal=terminal,truth_feasible=valid,truth_pointer_max_states=statecount,exact_recovery=original['plain_idx']==plain,recovery_fraction=sum(a==b for a,b in zip(original['plain_idx'],plain))/len(plain),source_gate=original['score']> -5.5,wrong_key=wrong_label,wrong_source=wrong,wrong_terminal=wrong_terminal,wrong_gate=wrong['score']> -5.5)
                    except Exception as exc:row.update(error_type=type(exc).__name__,error=str(exc))
                    rows.append(row)
        print('Positive fixture',fixture['id'],'attempts',len(rows),'elapsed',round(time.perf_counter()-started,3),flush=True)
    for label,key in keys:
        for sign in (-1,1):
            ct,plain,used=boundary(key,sign);original,terminal,beams=inspect(ct,key,sign,plain);explicit=n.padded(key,256);padded_result,padded_terminal,padded_beams=inspect(ct,explicit,sign,plain)
            assert beams==padded_beams and original==padded_result
            allocations=[]
            for L in (88,89,90,256):
                edge_beams,K=observe(ct[:L],key,sign=sign,o=0,beam_w=300,max_skip=3);expected=356+(4*L+8) if 4*L>=356 else 356;assert len(K)==expected and K==n.padded(key,L)
                allocations.append(dict(length=L,effective_key_length=len(K),terminal_count=len(edge_beams),winner_pointer=edge_beams[0][1]))
            boundaries.append(dict(key=label,sign=sign,ciphertext=ct,plain=plain,intended_accepted_pointers=used,intended_final_pointer=435,intended_truth_feasible=True,source=original,terminal=terminal,padded_source_equal=True,padded_ordered_terminals_equal=True,allocations=allocations))
    successful=[x for x in rows if 'error' not in x];summary=dict(attempts=len(rows),completed=len(successful),errors=len(rows)-len(successful),exact_recoveries=sum(x['exact_recovery'] for x in successful),source_gate_passes=sum(x['source_gate'] for x in successful),wrong_key_gate_passes=sum(x['wrong_gate'] for x in successful),truth_feasible=sum(x['truth_feasible'] for x in successful),truth_terminal=sum(x['terminal']['truth_in_terminal'] for x in successful),encoder_paths_over3=sum(max(x['skips'][1:],default=0)>3 for x in successful),boundary_cases=len(boundaries),allocation_checks=sum(len(x['allocations']) for x in boundaries))
    out=dict(stage='Frozen synthetic controls only; actual payload target bytes never staged/opened/scored',plan_sha256=sha(H/'controls-plan-frozen.json'),execution_sha256=sha(H/'controls-execution-frozen.json'),summary=summary,positive_cases=rows,boundaries=boundaries,seconds=time.perf_counter()-started,limits='Three fixtures reuse two known passages; synthetic256 is an invented concatenation. Boundary fixtures test admissibility/padding, not English recovery. Score passage is not correct plaintext. All failures/exceptions retained, no retries or parameter changes.')
    path=H/'controls-results.json';assert not path.exists();path.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n');print('CONTROLS COMPLETE',summary,'seconds',round(out['seconds'],3),flush=True)
if __name__=='__main__':main()
