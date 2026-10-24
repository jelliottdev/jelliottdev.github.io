"""Exactly source payload section1; explicit complete/error accounting and terminal diagnostic."""
import hashlib,json,time
from pathlib import Path
import native as n
from controls import inspect
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    plan=json.loads((H/'target-protocol-frozen.json').read_bytes())
    for p,h in plan['pins'].items():assert sha(H/p)==h,p
    assert not (H/'target-results.json').exists()
    inputs=[]
    for item in plan['targets']:
        raw=(H/item['path']).read_bytes();assert len(raw)==256 and hashlib.sha256(raw).hexdigest()==item['sha256']
        inputs.append((item['label'],[b%29 for b in raw]))
    constructors=json.loads((H/'key-constructor-receipt.json').read_bytes())
    started=time.perf_counter();rows=[]
    for label,values in inputs:
        for key_name,key in n.keys.items():
            assert len(key)==356
            for sign in (-1,1):
                for atb in (0,1):
                    assert time.perf_counter()-started<plan['runtime_limit_seconds']
                    case=dict(case=len(rows),payload=label,key=key_name,sign=sign,atbash=atb,key_sha256=hashlib.sha256(bytes(key)).hexdigest())
                    ct=[28-v for v in values] if atb else list(values)
                    try:
                        source,terminal,beams=inspect(ct,key,sign)
                        scores=[n.Q.score_norm(b[2]) for b in beams]
                        case.update(source=source,source_gate=source['score']> -5.5,terminal=terminal,terminal_normalized_scores=scores,normalized_gate=terminal['best_normalized_score']> -5.5)
                    except Exception as exc:case.update(error_type=type(exc).__name__,error=str(exc))
                    rows.append(case)
        print('Payload',label,'attempts',len(rows),'elapsed',round(time.perf_counter()-started,3),flush=True)
    ok=[x for x in rows if 'error' not in x];assert len(rows)==96
    best=max(ok,key=lambda x:x['source']['score']) if ok else None;bestnorm=max(ok,key=lambda x:x['terminal']['best_normalized_score']) if ok else None
    result=dict(stage='Authorized exact96-case source section1 target; historical diagnostic only',protocol_sha256=sha(H/'target-protocol-frozen.json'),attempts=96,completed=len(ok),errors=96-len(ok),source_gate_passes=sum(x['source_gate'] for x in ok),normalized_gate_passes=sum(x['normalized_gate'] for x in ok),retained_terminals=sum(x['terminal']['terminal_count'] for x in ok),normalized_improvements=sum(x['terminal']['best_normalized_score']>x['source']['score'] for x in ok),best_source_case=best['case'] if best else None,best_normalized_case=bestnorm['case'] if bestnorm else None,cases=rows,seconds=time.perf_counter()-started,limits=plan['purpose'])
    out=H/'target-results.json';out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n');print('TARGET COMPLETE',result['completed'],'/96 source hits',result['source_gate_passes'],'normalized hits',result['normalized_gate_passes'],'seconds',round(result['seconds'],3),flush=True)
if __name__=='__main__':main()
