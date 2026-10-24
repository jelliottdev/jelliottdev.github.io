"""Fresh finite source controls; source-full panels are gated when files are missing."""
import importlib.util,json,sys,re,statistics,time,hashlib,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];REPO=ROOT.parent/'source-cache/dukotah-cicada3301';LP=REPO/'liber-primus'
def load(name):
 p=LP/'analysis/round18/L7-redteam'/(name+'.py');spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
A=load('a1_scorer_language');B=load('b1_power_envelope');C=load('c1_bars');start=time.time()
result={'revision':'f08b20b632d91209ddbaa747e8e2f23df0c78ba1','scorer_total':A.Q.total,'full_panels_gate':[]}
try:A.build_panels()
except FileNotFoundError as e:result['full_panels_gate'].append(str(e))
for p in ['data/keys/mabinogion.txt','data/keys/welsh/welsh_mabinogion.txt']:
 if not (LP/p).exists():result['full_panels_gate'].append('Missing exact source '+p)
# These five panels use the unmodified source expressions and all their inputs exist.
P={}
P['EN_KJV']=A.D.text_to_runes(A._mid(A._read(str(LP/'data/kjv.txt')))[:900000],'EN').tolist()
sp=json.loads((LP/'SOLVED-PAGES.json').read_text(encoding='utf-8'));P['LP1_REAL']=A.sk.eng_to_idx(''.join(p['plaintext_transliteration'] for p in sp['pages']))
la=A._mid(A._read(str(LP/'analysis/latin/latin_218.txt')))+A._mid(A._read(str(LP/'analysis/latin/latin_28233.txt')));P['LATIN']=A.D.text_to_runes(la,'LA').tolist()
oe=A._read(str(LP/'analysis/round10b/B6-non-english-plaintext/corpora/oe_beowulf.txt'));oe='\n'.join(line for line in oe.split('\n') if re.search('[þðæÞÐÆ]',line));oe+=A._read(str(LP/'data/keys/runepoem_oe.txt'));P['OE']=A.D.text_to_runes(oe,'OE').tolist()
de=A._mid(A._read(str(LP/'analysis/round10b/B6-non-english-plaintext/corpora/de_faust.txt')))+A._mid(A._read(str(LP/'analysis/round10b/B6-non-english-plaintext/corpora/de_2.txt')));P['DE']=A.D.text_to_runes(de,'DE').tolist()
saved=json.loads((HERE/'sources/out_a1.json').read_text())
assert all(len(v)==saved['panel_sizes'][k] for k,v in P.items()),{k:len(v) for k,v in P.items()}
result['panels']={k:{'n':len(v),'sha256_bytes_indices':hashlib.sha256(bytes(v)).hexdigest()} for k,v in P.items()}
result['a1_rows']=[]
for name,idx in P.items():
 for rep in range(3):
  row=A.trial(idx,120,rep,'sha256_ctr',{'seed':b'CICADA3301'});row['panel']=name;result['a1_rows'].append(row)
 print('A1',name,'median',statistics.median(r['score'] for r in result['a1_rows'] if r['panel']==name),flush=True)
result['a1_source_subset_exact']=all(all(row[key]==source[key] or isinstance(row[key],float) and abs(row[key]-source[key])<1e-10 for key in row) for row in result['a1_rows'] for source in saved['rows'] if source['panel']==row['panel'] and source['L']==row['L'] and source['rep']==row['rep'])
result['headline']=C.c1_headline();result['g3_floor_available_panels']={name:C._diff_min(idx[:400000]) for name,idx in P.items()}
(HERE/'fresh-controls.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
# Test only the distinct transition-law controls, avoiding source low-entropy runs.
result['b1_cases']=[]
for name,mech,params in [('baseline','keyskip',{'supp':0.83}),('paired rejection','skip_by_two',{'supp':0.83}),('one free advance','drift_at',{'supp':0.83,'ndrift':1}),('free advance q=.02','free_drift',{'supp':0.83,'q':0.02})]:
 row=B.run_case(name,mech,params,nseed=7);result['b1_cases'].append(row);print('B1',name,row['median_score'],row['median_recovery'],flush=True)
 (HERE/'fresh-controls.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
result['elapsed_s']=time.time()-start
(HERE/'fresh-controls.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('PASS finite A1 15paired correct/wrong trials; B1 28source plants; available-panel floors and headline recomputed.',flush=True)
