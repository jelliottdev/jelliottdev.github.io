"""Independent complete synthetic payload controls; never reads real payloads."""
import argparse,hashlib,importlib.util,json,math,random,sys,time
from pathlib import Path
sys.dont_write_bytecode=True

def padded(key,length):return list(key)+[0]*(4*length+8) if 4*length>=len(key) else list(key)

def encoder(plain,key,sign,seed):
    rng=random.Random(seed);cipher=[];skips=[];used=[];pointer=0
    for rune in plain:
        rejected=0
        while True:
            c=(rune-sign*key[pointer])%29
            if cipher and c==cipher[-1] and rng.random()<.83:pointer+=1;rejected+=1;continue
            break
        cipher.append(c);skips.append(rejected);used.append(pointer);pointer+=1
    return cipher,skips,used

def pointers(cipher,plain,key,sign):
    if len(cipher)!=len(plain) or (cipher[0]+sign*key[0])%29!=plain[0]:return set(),0
    states={0};maximum=1
    for i in range(1,len(cipher)):
        nxt=set()
        for previous in states:
            for advance in range(1,5):
                accepted=previous+advance
                if accepted>=len(key):break
                if (cipher[i]+sign*key[accepted])%29==plain[i] and all((plain[i]-sign*key[t])%29==cipher[i-1] for t in range(previous+1,accepted)):nxt.add(accepted)
        states=nxt;maximum=max(maximum,len(states))
        if not states:break
    return states,maximum

def run(root):
    started=time.perf_counter();read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    plan=read(root/'controls-plan-frozen.json');execution=read(root/'controls-execution-frozen.json');report=read(root/'controls-results.json')
    for path,digest in {**plan['pins'],**execution['pins']}.items():assert sha(root/path)==digest,path
    assert report['plan_sha256']==sha(root/'controls-plan-frozen.json') and report['execution_sha256']==sha(root/'controls-execution-frozen.json')
    spec=importlib.util.spec_from_file_location('independent_payload_source',root/'native.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
    keys=list(n.keys.items());fixtures=read(root/'control-fixtures-frozen.json')['fixtures'];assert len(keys)==12 and len(fixtures)==3
    constructor=read(root/'key-constructor-receipt.json');assert [(r['label'],r['indices']) for r in constructor['key_rows']]==keys
    spelling={r[0]:r[2] for r in n.gp.GEMATRIA};counts={};total=0
    for line in (root/'source/liber-primus/data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():q,c=line.split();counts[q]=int(c);total+=int(c)
    logtotal=math.log10(total);model={q:math.log10(c)-logtotal for q,c in counts.items()};floor=math.log10(.01)-logtotal
    def score(text):
        if len(text)<4:return -999.
        value=0.
        for i in range(len(text)-3):value+=model.get(text[i:i+4],floor)
        return value/(len(text)-3)
    def beam(cipher,key,sign):
        key=padded(key,len(cipher));first=(cipher[0]+sign*key[0])%29;states=[(0.,0,spelling[first],[first],cipher[0])]
        for i in range(1,len(cipher)):
            following=[]
            for cumulative,previous,text,path,_ in states:
                for skipped in range(4):
                    accepted=previous+1+skipped
                    if accepted>=len(key):break
                    rune=(cipher[i]+sign*key[accepted])%29
                    if any((rune-sign*key[t])%29!=cipher[i-1] for t in range(previous+1,accepted)):continue
                    extended=text+spelling[rune];delta=0.
                    for end in range(max(4,len(text)+1),len(extended)+1):delta+=model.get(extended[end-4:end],floor)
                    following.append((cumulative+delta,accepted,extended,path+[rune],cipher[i]))
            assert following;following.sort(key=lambda t:t[0],reverse=True);states=following[:300]
        return states
    terminal_count=0;wrong_terminals=0;failures=[];wrong_passes=0;cases=report['positive_cases'];assert len(cases)==144
    def inspect(cipher,key,sign,original,terminal,truth=None):
        states=beam(cipher,key,sign);winner=states[0];value=score(winner[2]);norm=[score(t[2]) for t in states];best=max(range(len(norm)),key=lambda i:norm[i]);ranks=[i+1 for i,t in enumerate(states) if t[3]==truth] if truth is not None else []
        assert original==dict(score=value,beam_score=winner[0],plain_idx=winner[3],ptr_end=winner[1],translit=winner[2])
        assert terminal['terminal_ordered_sha256']==hashlib.sha256(json.dumps(states,separators=(',',':')).encode()).hexdigest()
        assert terminal['terminal_count']==len(states) and terminal['effective_key_length']==len(padded(key,len(cipher)))
        assert terminal['best_normalized_score']==norm[best] and terminal['best_normalized_rank']==best+1 and terminal['best_normalized_output']==states[best][3] and terminal['best_normalized_pointer']==states[best][1]
        assert terminal['truth_in_terminal']==bool(ranks) and terminal['truth_first_rank']==(ranks[0] if ranks else None)
        return states,norm
    for i,row in enumerate(cases):
        fi=i//48;j=(i%48)//4;sign=(-1,1)[(i%4)//2];atbash=i%2;fixture=fixtures[fi];label,key=keys[j];plain=fixture['indices']
        assert (row['case'],row['fixture'],row['key'],row['sign'],row['atbash'],row['seed'])==(i,fixture['id'],label,sign,atbash,plan['positive_matrix']['seed_start']+i)
        assert 'error' not in row
        cipher,skips,used=encoder(plain,padded(key,len(plain)),sign,row['seed']);actual=[28-c for c in cipher] if atbash else cipher
        assert actual==row['ciphertext'] and skips==row['skips'] and used==row['used'];states,norm=inspect(cipher,key,sign,row['source'],row['terminal'],plain);terminal_count+=len(states)
        valid,statecount=pointers(cipher,plain,padded(key,len(cipher)),sign);assert bool(valid)==row['truth_feasible'] and statecount==row['truth_pointer_max_states']
        assert row['exact_recovery']==(states[0][3]==plain) and row['recovery_fraction']==sum(a==b for a,b in zip(states[0][3],plain))/len(plain) and row['source_gate']==(norm[0]> -5.5)
        wrong_label,wrong_key=keys[(j+1)%12];assert row['wrong_key']==wrong_label
        wrong,_=inspect(cipher,wrong_key,sign,row['wrong_source'],row['wrong_terminal']);wrong_terminals+=len(wrong);assert row['wrong_gate']==(row['wrong_source']['score']> -5.5);wrong_passes+=row['wrong_gate']
        if not row['exact_recovery']:
            ranks=[k for k,t in enumerate(states) if t[3]==plain];assert ranks
            truth=states[ranks[0]];failures.append(dict(case=i,fixture=fixture['id'],key=label,sign=sign,atbash=atbash,truth_rank=ranks[0]+1,winner_cumulative=states[0][0],truth_cumulative=truth[0],strict_cumulative_preference=states[0][0]>truth[0],cumulative_tie=states[0][0]==truth[0],winner_normalized=norm[0],truth_normalized=norm[ranks[0]],normalized_winner_is_truth=row['terminal']['best_normalized_output']==plain))
        if (i+1)%48==0:print('Independent payload plants',i+1,'/144',flush=True)
    boundaries=report['boundaries'];assert len(boundaries)==24;allocation_checks=0;boundary_terminals=0
    for i,row in enumerate(boundaries):
        label,key=keys[i//2];sign=(-1,1)[i%2];assert row['key']==label and row['sign']==sign;effective=padded(key,256);cipher=[0];plain=[sign*effective[0]%29];used=[0];pointer=0;observed=set()
        for pos in range(1,256):
            skip=int(pos<=180)
            if skip:rune=(cipher[-1]+sign*effective[pointer+1])%29;observed.add(pointer+1)
            else:rune=(7*pos+3)%29
            pointer+=1+skip;used.append(pointer);observed.add(pointer);plain.append(rune);cipher.append((rune-sign*effective[pointer])%29)
        assert pointer==435 and {355,356,357}<=observed and row['intended_final_pointer']==435 and row['ciphertext']==cipher and row['plain']==plain and row['intended_accepted_pointers']==used
        reachable,_=pointers(cipher,plain,effective,sign);assert 435 in reachable and row['intended_truth_feasible']
        states,_=inspect(cipher,key,sign,row['source'],row['terminal'],plain);boundary_terminals+=len(states)
        assert states==beam(cipher,effective,sign) and row['padded_source_equal'] and row['padded_ordered_terminals_equal']
        for entry,length in zip(row['allocations'],(88,89,90,256)):
            expected=356+(4*length+8) if 4*length>=356 else 356;edge=beam(cipher[:length],key,sign)
            assert entry==dict(length=length,effective_key_length=expected,terminal_count=len(edge),winner_pointer=edge[0][1]);allocation_checks+=1
    expected=dict(attempts=144,completed=144,errors=0,exact_recoveries=sum(x['exact_recovery'] for x in cases),source_gate_passes=sum(x['source_gate'] for x in cases),wrong_key_gate_passes=wrong_passes,truth_feasible=sum(x['truth_feasible'] for x in cases),truth_terminal=sum(x['terminal']['truth_in_terminal'] for x in cases),encoder_paths_over3=sum(max(x['skips'][1:],default=0)>3 for x in cases),boundary_cases=24,allocation_checks=allocation_checks);assert expected==report['summary']
    return dict(status='PASS',control_plan_sha256=sha(root/'controls-plan-frozen.json'),execution_sha256=sha(root/'controls-execution-frozen.json'),controls_results_sha256=sha(root/'controls-results.json'),audit_script_sha256=sha(Path(__file__)),all144_encodings_and_signed_orientation_cases_verified=True,all_positive_and_wrong_key_ordered_terminal_hashes_verified=True,positive_terminal_hypotheses=terminal_count,wrong_key_terminal_hypotheses=wrong_terminals,boundary_terminal_hypotheses=boundary_terminals,all24_boundary_paths_and_explicit_padded_beams_verified=True,allocation_checks=allocation_checks,summary=expected,exact_recovery_failures=failures,actual_payload_opened_or_scored=False,limits='Complete synthetic control reconstruction; three fixtures reuse two readings. Boundary paths are arbitrary structural fixtures, not English recovery tests. A source score gate is not exact plaintext. Actual targets remain unauthorized by this receipt.',seconds=time.perf_counter()-started)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--producer-root',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);a=parser.parse_args();assert not a.output.exists();result=run(a.producer_root);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(result,indent=2))
