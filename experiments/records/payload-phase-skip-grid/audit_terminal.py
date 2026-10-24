"""Separately frozen post-target diagnostic; source selections unchanged."""
import json,time
import numpy as np
import engine as e
def main():
 plan={'classification':'Post-target normalized terminal-candidate audit, not altered source selection','source_result_sha256':e.sha(e.HERE/'results.json'),'ledger_sha256':e.sha(e.HERE/'outputs.jsonl'),'script_sha256':e.sha(e.HERE/'audit_terminal.py'),'method':'Run unchanged source beam with only return changed to expose all terminal states; checkoriginal cumulativewinner; scoreeveryretainedcandidate normalized; retainanyabove−5.5witness.'};pp=e.HERE/'terminal-plan.json'
 if pp.exists():assert json.loads(pp.read_text())==plan
 else:e.write(pp,plan)
 observer=e.terminal_observer();keys=e.keys();pages={p['id']:p['indices'] for p in json.loads((e.HERE/'pages.json').read_text())};full=[json.loads(line) for line in (e.HERE/'outputs.jsonl').read_text().splitlines() if '"stage":"full"' in line];rows=[];witness=[];t=time.perf_counter()
 for r in full:
  C=np.array(pages[r['page']]);C=28-C if r['atbash'] else C;states=observer(C,np.array(keys[r['stream']]),r['sign'],r['offset'],len(C),300);assert list(max(states,key=lambda x:x[0])[3])==r['plain'];scores=[(e.sweep.Q.score_norm(x[2]),x) for x in states];score,best=max(scores,key=lambda x:x[0]);row={k:r[k] for k in ['stream','page','sign','atbash','offset']};row.update(terminal_candidates=len(states),source_score=r['score'],best_normalized_score=score,best_plain=list(best[3]),changed_selection=list(best[3])!=r['plain'],above_gate=score> -5.5);rows.append(row)
  for normalized,state in scores:
   if normalized> -5.5:witness.append(row|{'score':normalized,'plain':list(state[3]),'transliteration':state[2],'cumulative_score':state[0]})
 result={'plan_sha256':e.sha(pp),'full_survivors':len(rows),'terminal_candidates':sum(r['terminal_candidates'] for r in rows),'different_selection':sum(r['changed_selection'] for r in rows),'above_gate_candidates':len(witness),'above_gate_survivors':sum(r['above_gate'] for r in rows),'best':max(rows,key=lambda x:x['best_normalized_score']),'rows':rows,'witnesses':witness};out=e.HERE/'terminal-audit.json'
 if out.exists():assert json.loads(out.read_text())==result
 else:e.write(out,result)
 print('Audit',result['terminal_candidates'],'candidates; abovegate',len(witness),'best',result['best']['best_normalized_score'],'elapsed',round(time.perf_counter()-t,2))
if __name__=='__main__':main()
