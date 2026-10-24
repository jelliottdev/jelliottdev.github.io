"""Complete independent scalar reconstruction of all96 payload target beams."""
import argparse,ast,copy,hashlib,json,math,time
from pathlib import Path
from audit_controls import padded,pointers

def run(root):
    started=time.perf_counter();read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    protocol=read(root/'target-protocol-frozen.json');result=read(root/'target-results.json')
    for name,digest in protocol['pins'].items():assert sha(root/name)==digest,name
    assert result['protocol_sha256']==sha(root/'target-protocol-frozen.json') and protocol['cases']==96
    gp=ast.parse((root/'source/liber-primus/src/lp/gematria.py').read_text(encoding='utf8'));table=ast.literal_eval(next(n.value for n in gp.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='GEMATRIA'));spelling={r[0]:r[2] for r in table}
    counts={};total=0
    for line in (root/'source/liber-primus/data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():q,c=line.split();counts[q]=int(c);total+=int(c)
    logtotal=math.log10(total);model={q:math.log10(c)-logtotal for q,c in counts.items()};floor=math.log10(.01)-logtotal
    # Reuse only this independent audit's already checked pure scalar oracle definitions.
    # No producer/native beam, scorer, target runner or target output enters the oracle.
    independent=Path(__file__).with_name('audit_controls.py');tree=ast.parse(independent.read_text(encoding='utf8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run');defs=[copy.deepcopy(n) for n in fn.body if isinstance(n,ast.FunctionDef) and n.name in ('score','beam')];assert len(defs)==2
    namespace=dict(model=model,spelling=spelling,floor=floor,padded=padded);exec(compile(ast.fix_missing_locations(ast.Module(body=defs,type_ignores=[])),'<independent-scalar-oracle>','exec'),namespace);beam=namespace['beam'];score=namespace['score']
    constructor=read(root/'key-constructor-receipt.json');keys=[(r['label'],r['indices']) for r in constructor['key_rows']];assert len(keys)==12 and len({tuple(k) for _,k in keys})==12 and all(len(k)==356 for _,k in keys)
    inputs=[]
    for item in protocol['targets']:
        raw=(root/item['path']).read_bytes();assert len(raw)==item['bytes']==256 and hashlib.sha256(raw).hexdigest()==item['sha256'];inputs.append((item['label'],[b%29 for b in raw]))
    cases=result['cases'];assert len(cases)==result['attempts']==96;completed=0;errors=0;source_hits=0;normalized_hits=0;terminal_count=0;improvements=0;source_scores=[];normalized_scores=[];tail_winners=0;tail_terminals=0
    for index,row in enumerate(cases):
        payload,values=inputs[index//48];label,key=keys[(index%48)//4];sign=(-1,1)[(index%4)//2];atbash=index%2
        assert (row['case'],row['payload'],row['key'],row['sign'],row['atbash'],row['key_sha256'])==(index,payload,label,sign,atbash,hashlib.sha256(bytes(key)).hexdigest())
        cipher=[28-v for v in values] if atbash else values
        try:states=beam(cipher,key,sign)
        except Exception as exc:
            assert row.get('error_type')==type(exc).__name__;errors+=1;source_scores.append(float('-inf'));normalized_scores.append(float('-inf'));continue
        assert 'error' not in row and all(len(s[3])==256 for s in states);completed+=1;first=states[0];norms=[score(s[2]) for s in states];best=max(range(len(states)),key=lambda i:norms[i]);terminal=row['terminal']
        expected=dict(score=norms[0],beam_score=first[0],plain_idx=first[3],ptr_end=first[1],translit=first[2]);assert expected==row['source']
        assert norms==row['terminal_normalized_scores']
        assert terminal==dict(terminal_count=len(states),terminal_ordered_sha256=hashlib.sha256(json.dumps(states,separators=(',',':')).encode()).hexdigest(),truth_in_terminal=False,truth_first_rank=None,best_normalized_score=norms[best],best_normalized_rank=best+1,best_normalized_output=states[best][3],best_normalized_pointer=states[best][1],effective_key_length=1388)
        effective=padded(key,256);assert len(effective)==1388 and effective[:356]==key and set(effective[356:])=={0}
        assert first[1] in pointers(cipher,first[3],effective,sign)[0] and states[best][1] in pointers(cipher,states[best][3],effective,sign)[0]
        assert row['source_gate']==(norms[0]> -5.5) and row['normalized_gate']==(norms[best]> -5.5)
        source_hits+=row['source_gate'];normalized_hits+=row['normalized_gate'];improvements+=norms[best]>norms[0];terminal_count+=len(states);tail_winners+=first[1]>=356;tail_terminals+=sum(s[1]>=356 for s in states);source_scores.append(norms[0]);normalized_scores.append(norms[best])
        if (index+1)%24==0:print('Independent complete payload beams',index+1,'/96',flush=True)
    assert completed==result['completed'] and errors==result['errors'] and source_hits==result['source_gate_passes'] and normalized_hits==result['normalized_gate_passes'] and terminal_count==result['retained_terminals'] and improvements==result['normalized_improvements']
    source_best=max(range(96),key=lambda i:source_scores[i]) if completed else None;norm_best=max(range(96),key=lambda i:normalized_scores[i]) if completed else None
    assert source_best==result['best_source_case'] and norm_best==result['best_normalized_case']
    return dict(status='PASS',target_protocol_sha256=sha(root/'target-protocol-frozen.json'),target_results_sha256=sha(root/'target-results.json'),audit_script_sha256=sha(Path(__file__)),independent_scalar_oracle_sha256=sha(independent),complete_target_beams=completed,exceptions=errors,all_ordered_terminal_hypotheses_reconstructed=terminal_count,all_complete256rune_outputs_scores_pointers_and_signed_orientations_exact=True,source_gate_passes=source_hits,normalized_gate_passes=normalized_hits,normalized_improvements=improvements,source_winners_using_zero_tail=tail_winners,retained_terminals_using_zero_tail=tail_terminals,best_source_case=source_best,best_source_score=source_scores[source_best] if completed else None,best_normalized_case=norm_best,best_normalized_score=normalized_scores[norm_best] if completed else None,coverage='Complete independent scalar reconstruction of all96target beams and every retained terminal hash/order/score; no sampling.',limits='Historical source section1diagnostic only. Seven strict control ranking losses retained; finite356symbol key prefix followed by source zero tail, no infinitely cycling extension. No language/message/cipher-family exclusion or whole-search significance claim; sections2-4unexecuted.',seconds=time.perf_counter()-started)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--producer-root',required=True,type=Path);parser.add_argument('--output',type=Path);parser.add_argument('--check-only',action='store_true');a=parser.parse_args();assert a.output or a.check_only
    if a.output:assert not a.output.exists(),'Refusing overwrite'
    result=run(a.producer_root)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(result,indent=2))
