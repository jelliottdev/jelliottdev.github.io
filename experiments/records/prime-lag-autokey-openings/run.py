"""Two frozen, bounded offline source-rule followups; not original full-campaign replay."""
import ast,csv,hashlib,json
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
plan=json.loads((HERE/'plan.json').read_bytes())
for r in plan['inputs']:assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
a=json.loads((ROOT/'data/index.json').read_bytes())['alphabet'];lookup={r['rune']:i for i,r in enumerate(a)};labels=[r['latin'] for r in a]
plain64=[int(r['output_index']) for r in csv.DictReader((ROOT/'exports/readings/warning.csv').read_text(encoding='utf-8-sig').splitlines())][:64];assert len(plain64)==64

pages=[]
for pid in plan['pages']:
 page=json.loads((ROOT/f'data/pages/{pid}.json').read_bytes());cipher=[lookup[c] for line in page['lines'] for c in line['raw'] if c in lookup];assert len(cipher)==page['rune_count'];pages.append((pid,cipher,[]))
# Dense source-rule autokey implementation.
def feedback(values,seed,lag,mode,encrypt=False):
 out=[]
 for i,v in enumerate(values):
  k=seed if i<lag else (out[i-lag] if encrypt else values[i-lag]) if mode=='ciphertext' else (values[i-lag] if encrypt else out[i-lag])
  out.append((v+k if encrypt else v-k)%29)
 return out
def independent(values,seed,lag,mode):
 if mode=='ciphertext':return [(v-(seed if i<lag else values[i-lag]))%29 for i,v in enumerate(values)]
 out=[]
 for i in range(len(values)):
  hops=i//lag;total=sum((1 if k%2==0 else -1)*values[i-k*lag] for k in range(hops+1));total+=(1 if (hops+1)%2==0 else -1)*seed;out.append(total%29)
 return out
settings=[(lag,mode,seed) for lag in plan['prime_lag_autokey']['lags'] for mode in plan['prime_lag_autokey']['modes'] for seed in plan['prime_lag_autokey']['primers']]
for lag,mode,seed in settings:
 c=feedback(plain64,seed,lag,mode,True);assert feedback(c,seed,lag,mode)==plain64 and independent(c,seed,lag,mode)==plain64
openings=json.loads((ROOT/'experiments/records/lp2-known-vigenere-keys/plan.json').read_bytes())['openings'];assert len(openings)==9 and all(len(o['indices'])==12 for o in openings)
match=[];equivalence=[];digest=hashlib.sha256();compares=0
for pid,cipher,_ in pages:
 if not cipher:continue
 groups={};long_groups=set()
 for lag,mode,seed in settings:
  p=feedback(cipher[:12],seed,lag,mode);assert p==independent(cipher[:12],seed,lag,mode);groups.setdefault(tuple(p),[]).append([lag,mode,seed])
  if lag>=13:long_groups.add(tuple(p))
  digest.update(pid.encode()+bytes([lag,seed,0 if mode=='ciphertext' else 1])+bytes(p))
  for o in openings:
   compares+=1
   if p==o['indices']:match.append({'page':pid,'lag':lag,'mode':mode,'single_rune_primer':seed,'opening':o['id']})
 assert len(long_groups)==29
 equivalence.append({'page':pid,'parameter_settings':len(settings),'distinct_predicted12_rune_prefixes':len(groups),'lag13_to31_parameter_settings':348,'lag13_to31_distinct_prefixes':len(long_groups),'prefix_equivalence_class_sizes':dict(Counter(map(len,groups.values())))})
write(HERE/'results.json',{'plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),'implementation':'Audited Python dense-rule reimplementation; original C++ runtime not compiled.','settings':len(settings),'exact64_rune_plant_controls_passed':len(settings),'independent_closed_form_plaintext_and_direct_ciphertext_checks':True,'page_settings':sum(bool(c) for _,c,_ in pages)*len(settings),'opening_comparisons':compares,'matches':match,'all_predicted_prefixes_digest':digest.hexdigest(),'equivalence_by_page':equivalence,'outcome':'bounded exact-opening compatibility result only','limit':'Six lag values13..31 never reach feedback within a12-rune opening and collapse to29 uniform-shift prefixes across348 parameter settings. All638 settings are not independent predicted openings. Only one-rune repeated primers,11 fixed lags, two modes and nine page-start cribs covered.'})

print(json.dumps({'settings':len(settings),'controls':len(settings),'opening_comparisons':compares,'exact_matches':len(match)},indent=2))
