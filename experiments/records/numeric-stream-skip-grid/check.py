"""Independent scalar beam and Latin quadgram checks; imports no source code."""
import hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
 result=json.loads((HERE/'results.json').read_text());assert result['plan_sha256']==hashlib.sha256((HERE/'frozen-plan.json').read_bytes()).hexdigest()
 labels=json.loads((HERE/'labels.json').read_text());labels={int(k):v for k,v in labels.items()};pages={x['id']:x['indices'] for x in json.loads((HERE/'pages.json').read_text())};keys={x['name']:x['key'] for x in json.loads((HERE/'streams.json').read_text())}
 counts={q:int(v) for q,v in [line.split() for line in (HERE/'source/liber-primus/data/english_quadgrams.txt').read_text().splitlines()]};norm=math.log10(sum(counts.values()));table={q:math.log10(v)-norm for q,v in counts.items()};floor=math.log10(.01)-norm
 def latin(P):return ''.join(labels[x] for x in P)
 def score(P):
  text=latin(P);return sum(table.get(text[j:j+4],floor) for j in range(len(text)-3))/(len(text)-3)
 def decode(C,K,sign,offset,length,width):
  first=(C[0]+sign*K[offset])%29;states=[(0.,offset,labels[first],(first,))]
  for i in range(1,length):
   candidates=[]
   for cumulative,pointer,text,path in states:
    for skipped in range(4):
     pos=pointer+1+skipped
     if pos>=len(K):break
     value=(C[i]+sign*K[pos])%29
     if any((value-sign*K[bypass])%29!=C[i-1] for bypass in range(pointer+1,pos)):continue
     new=text+labels[value];delta=sum(table.get(new[end-4:end],floor) for end in range(max(4,len(text)+1),len(new)+1))
     candidates.append((cumulative+delta,pos,new,path+(value,)))
   assert candidates
   candidates.sort(key=lambda x:x[0],reverse=True);states=candidates[:width]
  return list(max(states,key=lambda x:x[0])[3])
 rows=[json.loads(line) for line in (HERE/'outputs.jsonl').read_text().splitlines()];screen=[r for r in rows if r['stage']=='screen'];full=[r for r in rows if r['stage']=='full'];assert len(screen)==36300
 ident=lambda r:tuple(r[k] for k in ['stream','page','sign','atbash','offset'])
 assert len(set(ident(r) for r in screen))==36300
 assert {ident(r) for r in screen if r['score']> -6.5}=={ident(r) for r in full}
 maxdelta=0.
 for r in rows:
  delta=abs(score(r['plain'])-r['score']);maxdelta=max(maxdelta,delta);assert delta<2e-12
  assert len(r['plain'])==r['length']
 best=max(screen,key=lambda r:r['score']);assert best==result['best_screen'];assert max(full,key=lambda r:r['score'])==result['best_full']
 for r in full+[best]:
  C=pages[r['page']];C=[28-v for v in C] if r['atbash'] else C
  assert decode(C,keys[r['stream']],r['sign'],r['offset'],r['length'],60 if r['stage']=='screen' else 200)==r['plain'],ident(r)
 assert len(full)==result['full_survivors'] and sum(r['score']> -5.5 for r in full)==result['above_full_gate']
 print('PASS',len(rows),'independent scores; delta',maxdelta,';',len(full),'full paths and maximum screen independently reconstructed')
if __name__=='__main__':main()
