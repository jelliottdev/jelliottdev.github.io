"""Independent autokey encoder/frontier oracle and complete native control audit."""
import argparse,hashlib,importlib.util,json,math,random,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
from check_parity import native_terminals

def encode(plain,primer,mode,sign,seed):
    rng=random.Random(seed);cipher=[];skips=[];pointer=0;future=0;pastend=0;safety=0
    for i,p in enumerate(plain):
        rejected=0
        while True:
            if pointer<len(primer):key=primer[pointer]
            elif mode=='P':
                index=pointer-len(primer);future+=index>=i
                if index<len(plain):key=plain[index]
                else:key=0;pastend+=1
            else:
                index=pointer-len(primer)
                if index<len(cipher):key=cipher[index]
                else:key=0;future+=1
            c=(p-sign*key)%29
            if cipher and c==cipher[-1] and rng.random()<.83:
                pointer+=1;rejected+=1
                if rejected>40:safety+=1;break
                continue
            break
        cipher.append(c);skips.append(rejected);pointer+=1
    return cipher,skips,pointer,dict(future_key_queries=future,past_end_zero_queries=pastend,safety_breaks=safety)

def feasible(cipher,plain,primer,mode,sign):
    length=len(cipher);lp=len(primer);need=max(lp+length,4*length+8)
    def key(position,known):
        if position<lp:return primer[position]
        index=position-lp
        if mode=='P':return plain[index] if index<known else None
        return cipher[index] if index<length else 0
    if (cipher[0]+sign*primer[0])%29!=plain[0]:return False,0,0
    states={0};maximum=1
    for i in range(1,length):
        following=set()
        for previous in states:
            for step in range(1,5):
                accepted=previous+step
                if mode=='C' and accepted>=need:break
                value=key(accepted,i)
                if value is None:break
                if (cipher[i]+sign*value)%29!=plain[i]:continue
                if all(key(t,i) is not None and (plain[i]-sign*key(t,i))%29==cipher[i-1] for t in range(previous+1,accepted)):following.add(accepted)
        states=following;maximum=max(maximum,len(states))
        if not states:return False,maximum,i
    return True,maximum,None

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--producer-root',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);a=parser.parse_args();assert not a.output.exists();root=a.producer_root;started=time.perf_counter();read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    plan=read(root/'controls-plan-frozen.json');report=read(root/'controls-results.json')
    for path,digest in plan['pins'].items():assert sha(root/path)==digest,path
    assert report['plan_sha256']==sha(root/'controls-plan-frozen.json') and len(report['domain'])==360
    sys.path.insert(0,str(root.resolve()));spec=importlib.util.spec_from_file_location('independent_ak_controls_engine',root/'engine.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e);native=native_terminals(root,e.env)
    known={r['id']:sum([p['rune_indices'] for p in r['decoded_pages']],[]) for r in read(root/'known-readings.json')['controls'] if r['id'] in ('warning','lp2-56')}
    table={r[0]:r[2] for r in e.gp.GEMATRIA};counts={};total=0
    for line in (root/'source/liber-primus/data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():q,c=line.split();counts[q]=int(c);total+=int(c)
    logtotal=math.log10(total);scores={q:math.log10(c)-logtotal for q,c in counts.items()};floor=math.log10(.01)-logtotal
    def score(path):
        text=''.join(table[int(x)] for x in path);value=0.
        if len(text)<4:return -999.
        for i in range(len(text)-3):value+=scores.get(text[i:i+4],floor)
        return value/(len(text)-3)
    diagnostics=[];totals={mode:dict(total=0,exact=0,score_pass=0,truth_feasible=0,truth_terminal=0,wrong_score_pass=0,encoder_future_query_cases=0,past_end_zero_cases=0,encoder_skips_over3=0,safety_break_cases=0) for mode in ('P','C')};terminal_count=0;maxerror=0.;wrong_native=0
    expected_order=[(j,mode,sign,reading) for j in range(45) for mode in ('P','C') for sign in (-1,1) for reading in ('warning','lp2-56')]
    for index,row in enumerate(report['domain']):
        assert (row['primer_index'],row['mode'],row['sign'],row['reading'])==expected_order[index] and row['case']==index and row['seed']==plan['seed_start']+index
        assert (row['primer_label'],row['primer'])==e.primers()[row['primer_index']]
        truth=known[row['reading']];mode=row['mode'];cipher,skips,used,trace=encode(truth,row['primer'],mode,row['sign'],row['seed'])
        assert cipher==row['ciphertext'] and skips==row['skips'] and used==row['key_used_len']
        possible,statecount,first_failure=feasible(cipher,truth,row['primer'],mode,row['sign']);assert possible==row['truth_feasible'] and statecount==row['truth_pointer_max_states']
        terminals=native[mode](cipher,row['primer'],sign=row['sign'],beam_w=450,max_skip=3);terminal_count+=len(terminals);winner=terminals[0];assert list(winner[3])==row['output'] and winner[0]==row['cumulative'] and winner[1]==row['pointer']
        assert len(winner[3])==len(truth)==row['output_length'];value=score(winner[3]);maxerror=max(maxerror,abs(value-row['score']));assert value==row['score'] and (value> -5.5)==row['source_gate']
        assert (list(winner[3])==truth)==row['exact_recovery'] and sum(x==y for x,y in zip(winner[3],truth))/len(truth)==row['fraction']
        ranks=[i+1 for i,t in enumerate(terminals) if list(t[3])==truth];assert bool(ranks)==row['truth_in_terminal'] and (ranks[0] if ranks else None)==row['truth_first_cumulative_rank']
        norms=[score(t[3]) for t in terminals];best=max(range(len(norms)),key=lambda i:norms[i]);assert best+1==row['best_normalized_rank'] and norms[best]==row['best_normalized_score'] and list(terminals[best][3])==row['best_normalized_output']
        assert score(row['wrong_primer_output'])==row['wrong_primer_score'] and (row['wrong_primer_score']> -5.5)==row['wrong_primer_gate']
        wp=e.encode('MABINOGION');assert feasible(cipher,row['wrong_primer_output'],wp,mode,row['sign'])[0]
        if row['wrong_primer_gate']:
            bad=native[mode](cipher,wp,sign=row['sign'],beam_w=450,max_skip=3);assert list(bad[0][3])==row['wrong_primer_output'];wrong_native+=1
        t=totals[mode];t['total']+=1
        for field in ('exact_recovery','source_gate','truth_feasible','truth_in_terminal','wrong_primer_gate'):t[dict(exact_recovery='exact',source_gate='score_pass',truth_feasible='truth_feasible',truth_in_terminal='truth_terminal',wrong_primer_gate='wrong_score_pass')[field]]+=row[field]
        t['encoder_future_query_cases']+=trace['future_key_queries']>0;t['past_end_zero_cases']+=trace['past_end_zero_queries']>0;t['safety_break_cases']+=trace['safety_breaks']>0;t['encoder_skips_over3']+=max(skips[1:],default=0)>3
        if mode=='P':assert 0<=winner[1]-(len(truth)-1)<=len(row['primer'])-1
        diagnostics.append(dict(case=index,mode=mode,primer_label=row['primer_label'],truth_feasible=possible,first_truth_frontier_or_rule_failure=first_failure,**trace,encoder_max_skip=max(skips),complete_recovery=row['exact_recovery']))
        if (index+1)%60==0:print('Independent native complete controls',index+1,'/360',flush=True)
    for mode,t in totals.items():assert {k:t[k] for k in report['summary'][mode]}==report['summary'][mode]
    assert all(t['truth_feasible']==t['exact']==t['truth_terminal'] for t in totals.values())
    out=dict(status='PASS',plan_sha256=sha(root/'controls-plan-frozen.json'),controls_sha256=sha(root/'controls-results.json'),audit_sha256=sha(Path(__file__)),all360_rng_encodings_truth_feasibility_and_native_returned_paths_checked=True,native_terminal_hypotheses_checked=terminal_count,wrong_primer_gate_native_outputs_checked=wrong_native,maximum_independent_normalized_score_error=maxerror,all_outputs_complete=True,summary=totals,diagnostics=diagnostics,manuscript_loaded_or_scored=False,limits='Complete source-generated control audit. Infeasible true readings expose encoder/decoder mismatch, not detector pruning or a cipher-family rejection. Original90-rune gate does not validate these full-length cases.',seconds=time.perf_counter()-started)
    a.output.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps({k:v for k,v in out.items() if k!='diagnostics'},indent=2))

if __name__=='__main__':main()
