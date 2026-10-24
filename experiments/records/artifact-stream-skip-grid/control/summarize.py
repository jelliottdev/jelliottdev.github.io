"""Independent plant-construction receipts and descriptive cost estimates."""
import collections,hashlib,json,random,statistics,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    plan=json.loads((HERE/'plan-frozen.json').read_text());data=json.loads((HERE/'control-results.json').read_text());assert data['plan_sha256']==sha(HERE/'plan-frozen.json')
    readings=json.loads((HERE/'known-readings.json').read_text());streams=json.loads((HERE/'streams.json').read_text());lookup={(x['branch'],x['name']):x['key'] for x in streams};rows=data['rows']
    for r in rows:
        assert r['eligible'];P=readings[r['reading']];K=lookup[r['branch'],r['name']];rng=random.Random(r['seed']);C=[];skips=[];j=r['offset'];prev=None
        for p in P:
            n=0
            while True:
                c=(p-r['sign']*K[j])%29
                if prev is not None and c==prev and rng.random()<.83:j+=1;n+=1;continue
                break
            C.append(c);skips.append(n);prev=c;j+=1
        raw=[28-c for c in C] if r['atbash'] else C
        assert skips==r['skips'] and max(skips)<=3
        assert hashlib.sha256(struct.pack('<'+'q'*len(raw),*raw)).hexdigest()==r['cipher_sha256']
        assert r['screen_pass']==(r['screen_score']> -6.5)
        assert r['full_pass']==(r['full_score']> -5.5)
        assert r['source_success']==(r['screen_pass'] and r['full_pass'])
    summary={'plan_sha256':sha(HERE/'plan-frozen.json'),'results_sha256':sha(HERE/'control-results.json'),'independent_plant_reconstruction':len(rows),'elapsed_seconds':data['elapsed_seconds'],'branches':{},'recovery_failures':[{k:r[k] for k in ['branch','name','sign','atbash','offset','reading','seed','skip_total','skip_max','screen_exact','full_exact','screen_score','full_score']} for r in rows if not r['full_exact']],'phase_aliases':{}}
    for branch,count in [('numeric',36300),('numeric2A',23100)]:
        r=[x for x in rows if x['branch']==branch];fs=[x for x in r if not x['full_exact']]
        sm=statistics.mean(x['screen_seconds'] for x in r);fm=statistics.mean(x['full_seconds'] for x in r)
        # These timing projections are descriptive, not empirical manuscript bounds.
        max_per_rune=max(x['full_seconds']/len(readings[x['reading']]) for x in r)
        summary['branches'][branch]={'cells':len(r),'exact_complete_recovery':sum(x['full_exact'] for x in r),'exact_screen_recovery':sum(x['screen_exact'] for x in r),'screen_gate_pass':sum(x['screen_pass'] for x in r),'full_gate_pass':sum(x['full_pass'] for x in r),'source_both_gates_pass':sum(x['source_success'] for x in r),'zero_skip_plants':sum(x['skip_total']==0 for x in r),'wrong_key_both_gates_pass':sum(x['wrong_screen_score']> -6.5 and x['wrong_full_score']> -5.5 for x in r),'exact_recovery_failures_by_label':dict(collections.Counter(x['name'] for x in fs)),'screen_seconds_mean':sm,'screen_seconds_max':max(x['screen_seconds'] for x in r),'full_seconds_mean':fm,'full_seconds_max':max(x['full_seconds'] for x in r),'target_screen_settings':count,'screen_projection_at_measured_mean_seconds':sm*count,'screen_projection_at_measured_max_seconds':max(x['screen_seconds'] for x in r)*count,'confirmation_projection_if_one_percent_survive_at_measured_mean_seconds':count*.01*fm,'confirmation_projection_if_all_survive_at_longest_page_scaled_max_seconds':count*277*max_per_rune,'projection_warning':'Synthetic timings only; target branching and selection rates unknown. Longest-page scaling is an illustrative stress estimate, not a validated upper bound.'}
        aliases={}
        for stream in [x for x in streams if x['branch']==branch]:
            groups={}
            for off in range(5):groups.setdefault(bytes(stream['key'][off:off+1108]),[]).append(off)
            duplicates=[g for g in groups.values() if len(g)>1]
            if duplicates:aliases[stream['name']]=duplicates
        summary['phase_aliases'][branch]=aliases
    (HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['recovery_failures']},indent=2))
if __name__=='__main__':main()

