"""Exact source numeric2 Part B; --check preserves expected output bytes."""
import argparse,hashlib,json,time
import numpy as np
import engine as e
def execute():
 plan=json.loads((e.HERE/'frozen-plan.json').read_text());e.validate(plan);pages=json.loads((e.HERE/'pages.json').read_text());keys=e.keys();native=e.numeric.beam;rows=[];t=time.perf_counter()
 key_names={np.array(values,np.int64).tobytes():name for name,values in keys.items()};lookup={tuple(p['indices']):(p['id'],0) for p in pages};lookup.update({tuple(28-v for v in p['indices']):(p['id'],1) for p in pages})
 def capture(ct,K,sign,offset,length,width):
  path=native(ct,K,sign,offset,length,width);ident,atbash=lookup[tuple(map(int,ct))]
  rows.append({'stream':key_names[K.tobytes()],'page':ident,'sign':sign,'atbash':atbash,'offset':offset,'stage':'screen' if width==60 else 'full','length':length,'plain':path,'score':e.numeric.Q.score_norm(e.encoder.idx_to_trans(path))})
  return path
 e.numeric.beam=capture
 hits,best=e.numeric.sweep_payload_all_offsets(e.numeric.load_payload_bytes(),[np.array(p['indices'],np.int64) for p in pages]);e.numeric.beam=native
 screens=[r for r in rows if r['stage']=='screen'];full=[r for r in rows if r['stage']=='full'];identity=lambda r:tuple(r[k] for k in ['stream','page','sign','atbash','offset'])
 assert len(screens)==30112 and {identity(r) for r in screens if r['score']> -6.5}=={identity(r) for r in full}
 assert len(hits)==sum(r['score']> -5.5 for r in full) and best==max(r['score'] for r in screens)
 result={'plan_sha256':e.sha(e.HERE/'frozen-plan.json'),'screens':len(screens),'full_survivors':len(full),'source_gate_passes':len(hits),'best_screen':max(screens,key=lambda r:r['score']),'best_full':max(full,key=lambda r:r['score']) if full else None,'elapsed_seconds':time.perf_counter()-t}
 return result,''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows).encode('utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r,ledger=execute();expected=e.HERE/'results.json'
 if args.check:
  saved=json.loads(expected.read_text());assert {k:v for k,v in saved.items() if k!='elapsed_seconds'}=={k:v for k,v in r.items() if k!='elapsed_seconds'};assert (e.HERE/'outputs.jsonl').read_bytes()==ledger;print('PASS complete PartB source replay; expected files unchanged')
 else:assert not expected.exists();e.write(expected,r);(e.HERE/'outputs.jsonl').write_bytes(ledger)
 print(json.dumps({k:v for k,v in r.items() if k not in ['best_screen','best_full']},indent=2))
if __name__=='__main__':main()
