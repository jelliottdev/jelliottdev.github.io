"""Record the unchanged source numeric skip sweep. --check never writes outputs."""
import argparse,hashlib,json,sys,time
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def setup():
 plan=json.loads((HERE/'frozen-plan.json').read_text(encoding='utf-8'))
 for item in plan['inputs']:assert sha(HERE/item['path'])==item['sha256'],item['path']
 source=HERE/'source/liber-primus';sys.path[:0]=[str(source/'analysis/campaign18_skip/armada'),str(source/'analysis/campaign18_skip'),str(source/'analysis'),str(source/'src')]
 import numeric_skip as m
 pages=json.loads((HERE/'pages.json').read_text());keys=json.loads((HERE/'streams.json').read_text())
 assert [(n,list(map(int,k))) for n,k in m.build_catalog(1176,False)]==[(x['name'],x['key']) for x in keys]
 assert m.SCREEN_LEN==50 and m.SCREEN_BW==60 and m.FULL_BW==200 and m.OFFSETS==[0,1,2,3,4] and m.SCREEN_THR==-6.5 and m.CONFIRM_THR==-5.5
 return plan,m,pages,keys
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();plan,m,pages,keys=setup();native=m.beam;rows=[];logs=[];t=time.perf_counter()
 lookup={tuple(p['indices']):(p['id'],0) for p in pages};lookup.update({tuple(28-v for v in p['indices']):(p['id'],1) for p in pages})
 for key in keys:
  def capture(ct,K,sign,offset,length,width):
   out=native(ct,K,sign,offset,length,width);ident,atb=lookup[tuple(map(int,ct))]
   rows.append({'stream':key['name'],'page':ident,'sign':sign,'atbash':atb,'offset':offset,'stage':'screen' if width==60 else 'full','length':length,'plain':out,'score':m.Q.score_norm(m.idx_to_trans(out))})
   return out
  m.beam=capture
  hits,best=m.sweep_keystream(key['name'],np.array(key['key'],np.int64),[np.array(p['indices'],np.int64) for p in pages])
  logs.append({'stream':key['name'],'screens':sum(r['stage']=='screen' for r in rows if r['stream']==key['name']),'full_survivors':sum(r['stage']=='full' for r in rows if r['stream']==key['name']),'source_best_screen':best,'source_full_hits':len(hits)})
  print(key['name'],logs[-1]['full_survivors'],'confirmations',flush=True)
 screens=[r for r in rows if r['stage']=='screen'];full=[r for r in rows if r['stage']=='full'];assert len(screens)==36300
 identity=lambda r:tuple(r[k] for k in ['stream','page','sign','atbash','offset'])
 assert {identity(r) for r in screens if r['score']> -6.5}=={identity(r) for r in full}
 result={'plan_sha256':sha(HERE/'frozen-plan.json'),'screen_count':len(screens),'full_survivors':len(full),'above_full_gate':sum(r['score']> -5.5 for r in full),'best_screen':max(screens,key=lambda r:r['score']),'best_full':max(full,key=lambda r:r['score']) if full else None,'stream_logs':logs}
 payload=''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows).encode('utf-8')
 if args.check:
  assert json.loads((HERE/'results.json').read_text())==result
  assert (HERE/'outputs.jsonl').read_bytes()==payload
  print('PASS full source replay: all deterministic rows/results identical; expected outputs untouched')
 else:
  assert not (HERE/'results.json').exists(),'Expected outputs already exist; use --check'
  (HERE/'outputs.jsonl').write_bytes(payload);(HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');(HERE/'timing.json').write_text(json.dumps({'elapsed_seconds':time.perf_counter()-t},indent=2)+'\n',encoding='utf-8',newline='\n')
 print('Elapsed',round(time.perf_counter()-t,3),'seconds; screens',len(screens),'full',len(full),'hits',result['above_full_gate'])
if __name__=='__main__':main()
