"""Post-target audit: normalized scores of every retained terminal candidate.

The historical source-selected result is never replaced. Source beam code is
executed in memory with only its final return value changed to expose states.
"""
import hashlib,inspect,json,time
from pathlib import Path
import numpy as np
import run
HERE=Path(__file__).resolve().parent
def main():
 plan,m,pages,keys=run.setup();pmap={x['id']:x['indices'] for x in pages};kmap={x['name']:x['key'] for x in keys};survivors=[json.loads(line) for line in (HERE/'outputs.jsonl').read_text().splitlines() if '"stage":"full"' in line]
 auditplan={'classification':'Post-target terminal-candidate audit; source-selected outputs and gates unchanged','result_sha256':run.sha(HERE/'results.json'),'ledger_sha256':run.sha(HERE/'outputs.jsonl'),'audit_script_sha256':run.sha(Path(__file__)),'method':'Same source beam, only return all retained terminal states; re-score every candidate by normalized English quadgrams, retain maximum. Check original maximum-cumulative winner still equals saved path. Report all best-normalized paths and all candidates above−5.5. No wider beam or new settings.'}
 text=json.dumps(auditplan,indent=2)+'\n';pf=HERE/'terminal-audit-plan.json'
 if pf.exists():assert pf.read_text()==text
 else:pf.write_text(text,encoding='utf-8',newline='\n')
 code=inspect.getsource(m.beam);assert code.count('return list(best[3])')==1
 space=dict(m.beam.__globals__);exec(code.replace('return list(best[3])','return beams'),space);beam=space['beam'];rows=[];witness=[];t=time.perf_counter()
 for r in survivors:
  C=np.array(pmap[r['page']],np.int64);C=28-C if r['atbash'] else C;states=beam(C,np.array(kmap[r['stream']]),r['sign'],r['offset'],len(C),200)
  selected=max(states,key=lambda x:x[0]);assert list(selected[3])==r['plain']
  scored=[(m.Q.score_norm(x[2]),x) for x in states];score,best=max(scored,key=lambda x:x[0]);entry={k:r[k] for k in ['stream','page','sign','atbash','offset']}
  entry.update(terminal_candidates=len(states),source_score=r['score'],best_normalized_score=score,best_plain=list(best[3]),best_transliteration=best[2],source_selection_changed=list(best[3])!=r['plain'],above_gate=score> -5.5);rows.append(entry)
  for normalized,state in scored:
   if normalized> -5.5:witness.append(entry|{'score':normalized,'plain':list(state[3]),'transliteration':state[2],'cumulative_score':state[0]})
 result={'audit_plan_sha256':run.sha(pf),'survivors':len(rows),'terminal_candidates':sum(x['terminal_candidates'] for x in rows),'above_gate_survivors':sum(x['above_gate'] for x in rows),'above_gate_candidates':len(witness),'different_selection_survivors':sum(x['source_selection_changed'] for x in rows),'best':max(rows,key=lambda x:x['best_normalized_score']),'rows':rows,'witnesses':witness}
 target=HERE/'terminal-audit.json';payload=json.dumps(result,indent=2)+'\n'
 if target.exists():assert target.read_text()==payload
 else:target.write_text(payload,encoding='utf-8',newline='\n')
 print('AUDIT',len(rows),'survivors;',result['terminal_candidates'],'terminal candidates; abovegate',len(witness),'best',result['best']['best_normalized_score'],'elapsed',round(time.perf_counter()-t,3))
if __name__=='__main__':main()
