"""Portable unchanged-source known-reading controls; --check never writes."""
import argparse,hashlib,json,time
import numpy as np
import engine as e
def execute():
 plan=json.loads((e.HERE/'control-plan.json').read_text());e.validate(plan);keys=e.keys();names=list(keys);known=json.loads((e.HERE/'known-readings.json').read_text());rows=[];t=time.perf_counter()
 for ni,name in enumerate(names):
  K=keys[name];wrong=keys[names[(ni+1)%4]]
  for sign in [-1,1]:
   for offset in range(202):
    reading='warning' if (ni+offset)%2==0 else 'lp2-56';P=known[reading];C=None;first=None
    for seed in range(3301,3333):
     cc,sk,used=e.encoder.encipher_keyskip(P,K[offset:],sign=sign,supp=.83,seed=seed)
     if first is None:first=max(sk)
     if max(sk)<=3:C=cc;break
    row={'stream':name,'sign':sign,'offset':offset,'reading':reading,'eligible':C is not None,'attempts':seed-3300,'initial_max_skip':first}
    if C is not None:
     start=time.perf_counter();short=e.sweep.beam(np.array(C),np.array(K),sign,offset,50,60);st=time.perf_counter()-start
     start=time.perf_counter();full=e.sweep.beam(np.array(C),np.array(K),sign,offset,len(P),300);ft=time.perf_counter()-start
     ws=e.sweep.beam(np.array(C),np.array(wrong),sign,offset,50,60);wf=e.sweep.beam(np.array(C),np.array(wrong),sign,offset,len(P),300)
     score=lambda values:e.sweep.Q.score_norm(e.encoder.idx_to_trans(values))
     ss,fs=score(short),score(full)
     row.update(seed=seed,skips=sk,used=used,cipher=C,skip_total=sum(sk),skip_max=max(sk),screen_exact=short==P[:50],full_exact=full==P,screen_score=ss,full_score=fs,screen_pass=ss> -6.5,full_pass=fs> -5.5,both_gates=ss> -6.5 and fs> -5.5,plain=full,plain_sha256=hashlib.sha256(bytes(full)).hexdigest(),wrong_screen=score(ws),wrong_full=score(wf),screen_seconds=st,full_seconds=ft)
     if offset in [0,201]:
      # Reversal of Atbash preprocessing restores this exact decoder input.
      reflected=28-np.array(C);restored=28-reflected;assert restored.tolist()==C
      again=e.sweep.beam(restored,np.array(K),sign,offset,len(P),300);assert again==full
      row['atbash_parity']=True
    rows.append(row)
   print('Controls',name,sign,'done',round(time.perf_counter()-t,2),'s',flush=True)
 eligible=[r for r in rows if r['eligible']]
 return {'control_plan_sha256':e.sha(e.HERE/'control-plan.json'),'cells':len(rows),'eligible':len(eligible),'no_eligible':len(rows)-len(eligible),'exact_full':sum(r['full_exact'] for r in eligible),'exact_screen':sum(r['screen_exact'] for r in eligible),'screen_pass':sum(r['screen_pass'] for r in eligible),'full_pass':sum(r['full_pass'] for r in eligible),'both_gates':sum(r['both_gates'] for r in eligible),'zero_skip':sum(r['skip_total']==0 for r in eligible),'wrong_both_gates':sum(r['wrong_screen']> -6.5 and r['wrong_full']> -5.5 for r in eligible),'atbash_parity':sum(r.get('atbash_parity',False) for r in rows),'elapsed_seconds':time.perf_counter()-t,'rows':rows}
def deterministic(x):
 if isinstance(x,dict):return {k:deterministic(v) for k,v in x.items() if k not in ['elapsed_seconds','screen_seconds','full_seconds']}
 if isinstance(x,list):return [deterministic(v) for v in x]
 return x
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=execute();p=e.HERE/'control-results.json'
 if args.check:assert deterministic(json.loads(p.read_text()))==deterministic(r);print('PASS all1616 control cells; expected files unchanged')
 else:assert not p.exists();e.write(p,r)
 print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
