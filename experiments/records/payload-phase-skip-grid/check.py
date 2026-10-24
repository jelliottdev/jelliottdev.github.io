"""Independent scalar decoder, scores and plant checks; no source functions."""
import hashlib,json,math,random
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
 keys=json.loads((HERE/'streams.json').read_text());pages={p['id']:p['indices'] for p in json.loads((HERE/'pages.json').read_text())};labels={int(k):v for k,v in json.loads((HERE/'labels.json').read_text()).items()};known=json.loads((HERE/'known-readings.json').read_text())
 counts={q:int(v) for q,v in [line.split() for line in (HERE/'source/liber-primus/data/english_quadgrams.txt').read_text().splitlines()]};norm=math.log10(sum(counts.values()));table={q:math.log10(v)-norm for q,v in counts.items()};floor=math.log10(.01)-norm
 def text(P):return ''.join(labels[x] for x in P)
 def cumulative(P):
  value=text(P);return sum(table.get(value[j:j+4],floor) for j in range(len(value)-3))
 def score(P):return cumulative(P)/(len(text(P))-3)
 def beam(C,K,sign,offset,length,width):
  initial=(C[0]+sign*K[offset])%29;states=[(0.,offset,labels[initial],(initial,))]
  for i in range(1,length):
   candidates=[]
   for total,pointer,latin,path in states:
    for skip in range(4):
     pos=pointer+1+skip
     if pos>=len(K):break
     value=(C[i]+sign*K[pos])%29
     if any((value-sign*K[j])%29!=C[i-1] for j in range(pointer+1,pos)):continue
     extended=latin+labels[value];delta=sum(table.get(extended[j-4:j],floor) for j in range(max(4,len(latin)+1),len(extended)+1))
     candidates.append((total+delta,pos,extended,path+(value,)))
   assert candidates;candidates.sort(key=lambda x:x[0],reverse=True);states=candidates[:width]
  return states
 raw=(HERE/'source/liber-primus/analysis/pp49_51/canon_256.bin').read_bytes();other=(HERE/'source/liber-primus/analysis/pp49_51/canon_256_decpref.bin').read_bytes()
 originals={'payload_majority':raw,'payload_majority_rev':raw[::-1],'payload_decpref':other,'payload_decpref_rev':other[::-1]}
 assert keys=={name:[value%29 for value in data]*7 for name,data in originals.items()}
 cycles={bytes((sign*data[(off+j)%256])%29 for j in range(256)) for data in originals.values() for sign in [-1,1] for off in range(256)};assert len(cycles)==2048
 runes='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ';segments=[[runes.index(ch) for ch in part if ch in runes] for part in (HERE/'source/liber-primus/data/krisyotam_runes.txt').read_text(encoding='utf-8').split('%')];segments=[part for part in segments if part][:-2];assert segments==list(pages.values())
 controls=json.loads((HERE/'control-results.json').read_text());assert controls['control_plan_sha256']==hashlib.sha256((HERE/'control-plan.json').read_bytes()).hexdigest();failures=[]
 for r in controls['rows']:
  assert r['eligible'];P=known[r['reading']];K=keys[r['stream']];rng=random.Random(r['seed']);C=[];sk=[];used=[];j=r['offset'];previous=None
  for value in P:
   skip=0
   while True:
    c=(value-r['sign']*K[j])%29
    if previous is not None and c==previous and rng.random()<.83:j+=1;skip+=1;continue
    break
   C.append(c);sk.append(skip);used.append(j-r['offset']);j+=1;previous=c
  assert (C,sk,used)==(r['cipher'],r['skips'],r['used']) and max(sk)<=3
  assert r['full_exact']==(r['plain']==P) and hashlib.sha256(bytes(r['plain'])).hexdigest()==r['plain_sha256'];assert abs(score(r['plain'])-r['full_score'])<2e-12
  if not r['full_exact']:
   for i in range(1,len(P)):
    for pos in range(used[i-1]+1,used[i]):assert (P[i]-r['sign']*K[r['offset']+pos])%29==C[i-1]
   states=beam(C,K,r['sign'],r['offset'],len(P),300);winner=max(states,key=lambda x:x[0]);assert list(winner[3])==r['plain'];ranks=[i for i,state in enumerate(states,1) if list(state[3])==P];delta=cumulative(r['plain'])-cumulative(P)
   failures.append({'stream':r['stream'],'sign':r['sign'],'offset':r['offset'],'true_valid':True,'true_survives':bool(ranks),'true_rank':ranks[0] if ranks else None,'genuine_skips':sum(sk)>0,'cumulative_delta':delta,'classification':'tie' if abs(delta)<1e-10 else ('strictly_higher_alternative' if delta>0 else 'lower_scoring_alternative'),'chosen_normalized_below_truth':score(r['plain'])<score(P)-1e-12})
 rows=[json.loads(line) for line in (HERE/'outputs.jsonl').read_text().splitlines()];screens=[r for r in rows if r['stage']=='screen'];full=[r for r in rows if r['stage']=='full'];result=json.loads((HERE/'results.json').read_text());assert result['plan_sha256']==hashlib.sha256((HERE/'frozen-plan.json').read_bytes()).hexdigest();identity=lambda r:tuple(r[k] for k in ['stream','page','sign','atbash','offset'])
 expected={(stream,page,sign,atb,off) for stream in keys for page,P in pages.items() for sign in [-1,1] for atb in [0,1] for off in range(max(1,268-len(P)))}
 assert set(identity(r) for r in screens)==expected and len(screens)==len(expected)==30112
 assert {identity(r) for r in screens if r['score']> -6.5}=={identity(r) for r in full}
 maxdelta=0.
 for r in rows:
  assert len(r['plain'])==r['length'];delta=abs(score(r['plain'])-r['score']);maxdelta=max(maxdelta,delta);assert delta<2e-12
 maximum=max(screens,key=lambda r:r['score']);assert maximum==result['best_screen'] and max(full,key=lambda r:r['score'])==result['best_full']
 audit=json.loads((HERE/'terminal-audit.json').read_text()) if (HERE/'terminal-audit.json').exists() else None
 audited={identity(r):r for r in audit['rows']} if audit else {}
 for r in full+[maximum]:
  C=pages[r['page']];C=[28-v for v in C] if r['atbash'] else C;states=beam(C,keys[r['stream']],r['sign'],r['offset'],r['length'],60 if r['stage']=='screen' else 300)
  assert list(max(states,key=lambda x:x[0])[3])==r['plain'],identity(r)
  if r['stage']=='full' and audit:
   value=max(states,key=lambda state:score(state[3]));saved=audited[identity(r)]
   assert len(states)==saved['terminal_candidates'] and list(value[3])==saved['best_plain']
   assert abs(score(value[3])-saved['best_normalized_score'])<2e-12
 assert result['screens']==len(screens) and result['full_survivors']==len(full) and result['source_gate_passes']==sum(r['score']> -5.5 for r in full)
 receipt={'control_plants_reconstructed':len(controls['rows']),'control_recovery_failures':failures,'target_outputs_rescored':len(rows),'target_max_score_delta':maxdelta,'full_paths_reconstructed':len(full),'maximum_screen_reconstructed':True}
 path=HERE/'independent-check.json'
 if path.exists():assert json.loads(path.read_text())==receipt
 else:path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
 from collections import Counter
 print('PASS independent',len(controls['rows']),'plants;',len(rows),'scores;',len(full),'full paths; failures',Counter(r['classification'] for r in failures),'truth retained',sum(r['true_survives'] for r in failures))
if __name__=='__main__':main()
