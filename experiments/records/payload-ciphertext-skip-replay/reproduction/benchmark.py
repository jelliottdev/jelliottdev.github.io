"""Native complete96-cell timing grid on frozen synthetic bytes only."""
import hashlib,json,random,time
from pathlib import Path
import native as n
H=Path(__file__).resolve().parent

if __name__=='__main__':
    plan=json.loads((H/'benchmark-plan-frozen.json').read_bytes())
    for path,digest in plan['pins'].items():assert hashlib.sha256((H/path).read_bytes()).hexdigest()==digest,path
    started=time.perf_counter();rows=[];fixtures=[]
    for seed in plan['synthetic_byte_seeds']:
        rng=random.Random(seed);raw=bytes(rng.randrange(256) for _ in range(256));cipher=[x%29 for x in raw];fixtures.append(dict(seed=seed,synthetic_byte_sha256=hashlib.sha256(raw).hexdigest(),indices_uint8_sha256=hashlib.sha256(bytes(cipher)).hexdigest()))
        for label,key in n.keys.items():
            for sign in (-1,1):
                for atbash in (0,1):
                    ct=[28-x for x in cipher] if atbash else cipher;t=time.perf_counter();result=n.decode(ct,key,sign=sign,o=0,beam_w=300,max_skip=3)
                    rows.append(dict(fixture_seed=seed,key=label,sign=sign,atbash=atbash,seconds=time.perf_counter()-t,output_length=len(result['plain_idx']),pointer=result['ptr_end'],score=result['score'],output_uint8_sha256=hashlib.sha256(bytes(result['plain_idx'])).hexdigest()))
        print('Synthetic fixture completed',seed,'calls',len(rows),flush=True)
    assert len(rows)==96 and all(row['output_length']==256 for row in rows)
    result=dict(stage='Native synthetic benchmark only; no actual payload target bytes opened or scored',plan_sha256=hashlib.sha256((H/'benchmark-plan-frozen.json').read_bytes()).hexdigest(),calls=96,fixtures=fixtures,rows=rows,elapsed_seconds=time.perf_counter()-started,maximum_call_seconds=max(r['seconds'] for r in rows),pointer_beyond356_cases=sum(r['pointer']>=356 for r in rows),target_time_estimate='Measured96synthetic calls, not a guarantee for actualtarget; no acceleration or beam adjustment',actual_payload_opened_or_scored=False)
    out=H/'benchmark-results.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n');print('PASS native96synthetic benchmark',round(result['elapsed_seconds'],3),'seconds')
