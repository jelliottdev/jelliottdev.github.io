"""Post-target exploratory whole-key-search calibration; original target files immutable."""
import argparse,csv,hashlib,json,random,re,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PLAN=json.loads((HERE/'calibration-plan.json').read_bytes())
for r in PLAN['inputs']:assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']
a=json.loads((ROOT/'data/index.json').read_bytes())['alphabet'];lookup={r['rune']:i for i,r in enumerate(a)};labels=[r['latin'] for r in a]
lexicon={w.upper() for w in (ROOT/'experiments/records/rail-fence-visible-words/lexicon.txt').read_text(encoding='ascii').splitlines() if len(w)>=3}
keys=PLAN['clean_keywords'];sourcekeys=PLAN['source_keywords'];assert len(keys)==45

def permutation(n,key):
 positions=sorted(range(n),key=lambda i:(key[i%len(key)],i%len(key),i//len(key)));out=[0]*n
 for j,i in enumerate(positions):out[i]=j
 return out

def encrypt(p,key):return [p[i] for i in sorted(range(len(p)),key=lambda i:(key[i%len(key)],i%len(key),i//len(key)))]

def decrypt(c,key):return [c[j] for j in permutation(len(c),key)]

def score(p,lengths):
 i=hits=0
 for n in lengths:
  word=''.join(labels[v] for v in p[i:i+n]);hits+=word in lexicon;i+=n
 assert i==len(p)
 return hits

pages=[]
for i in range(56):
 page=json.loads((ROOT/f'data/pages/lp2-{i:02d}.json').read_bytes());raw=''.join(l['raw'] for l in page['lines']).replace('/','');ws=[[lookup[c] for c in w if c in lookup] for w in raw.split('-')];ws=[w for w in ws if w];flat=[v for w in ws for v in w]
 assert len(flat)==page['rune_count']
 if flat:pages.append((page['id'],flat,[len(w) for w in ws]))
assert len(pages)==55
permutations={(len(c),key):permutation(len(c),key) for _,c,_ in pages for key in set(keys)}

def aggregate(page_values):
 totals=[0]*45
 for (_,_,lengths),c in zip(pages,page_values):
  cached={}
  for i,key in enumerate(keys):
   perm=tuple(permutations[(len(c),key)])
   if perm not in cached:cached[perm]=score([c[j] for j in perm],lengths)
   totals[i]+=cached[perm]
 return totals

def shuffled_trial(rng):
 seq=[]
 for _,c,_ in pages:
  shuffled=list(c);rng.shuffle(shuffled);assert sorted(shuffled)==sorted(c);seq.append(shuffled)
 totals=aggregate(seq)
 return {'per_keyword_hits':totals,'global_key_maximum':max(totals)}

def original_unchanged():
 for r in PLAN['inputs']:assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']

def controls():
 warning=json.loads((ROOT/'data/pages/lp1-01.json').read_bytes());raw=''.join(l['raw'] for l in warning['lines']).replace('/','')
 parts=re.split('[^'+''.join(re.escape(c) for c in lookup)+']+',raw);parts=[p for p in parts if p];lengths=[len(p) for p in parts]
 plain=[int(r['output_index']) for r in csv.DictReader((ROOT/'exports/readings/warning.csv').read_text(encoding='utf-8-sig').splitlines())]
 cipher=[lookup[c] for p in parts for c in p]
 assert len(plain)==len(cipher)==warning['rune_count']==sum(lengths)
 assert plain==[28-c for c in cipher] # existing Warning Atbash trace, no spelling edits
 direct=score(plain,lengths);rows=[]
 for plant_label,plant_key in zip(sourcekeys,keys):
  c=encrypt(plain,plant_key);counts=[score(decrypt(c,key),lengths) for key in keys];out=decrypt(c,plant_key);assert out==plain
  true=count=score(out,lengths);better=sum(v>true for v in counts);tied=[k for k,v in zip(sourcekeys,counts) if v==true]
  rows.append({'planted_source_keyword':plant_label,'clean_keyword':plant_key,'true_plaintext_hits':true,'best_hits':max(counts),'true_rank_competition':better+1,'labels_tied_at_true_score':tied,'true_map_is_top_ranked':better==0,'exact_plaintext_recovered':True,'all_key_scores':counts,'equivalent_position_map_labels':[label for label,key in zip(sourcekeys,keys) if permutation(len(c),key)==permutation(len(c),plant_key)]})
 return {'reading':'Warning','runes':len(plain),'word_slots':len(lengths),'word_lengths':lengths,'direct_canonical_words':[''.join(labels[v] for v in plain[sum(lengths[:i]):sum(lengths[:i+1])]) for i in range(len(lengths))],'direct_dictionary_hits':direct,'score_rank_controls':len(rows),'true_top_ranked':sum(r['true_map_is_top_ranked'] for r in rows),'exact_recovered':sum(r['exact_plaintext_recovered'] for r in rows),'ranked_rows':rows,'limit':'Post-target score/rank calibration on one existing reading and its fixed boundaries; not a general-language power bound.'}

arg=argparse.ArgumentParser();arg.add_argument('--benchmark',action='store_true');args=arg.parse_args()
if args.benchmark:
 start=time.perf_counter();shuffled_trial(random.Random(PLAN['seed']));seconds=time.perf_counter()-start;result={'seconds_one_full45_key_trial':seconds,'estimated128_trial_seconds':seconds*128,'method':'One complete shared55-page shuffle with all45-label/43-order aggregate dictionary scores; no parameter tuning.'};(HERE/'calibration-benchmark.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');original_unchanged();print(json.dumps(result,indent=2))
else:
 observed=aggregate([c for _,c,_ in pages]);original=json.loads((HERE/'results.json').read_bytes());assert observed==[r['hits'] for r in original['per_keyword_totals']];assert max(observed)==original['maximum_raw_hits']==126
 positive=controls();rng=random.Random(PLAN['seed']);start=time.perf_counter();trials=[shuffled_trial(rng) for _ in range(PLAN['null_replicates'])];elapsed=time.perf_counter()-start
 maxima=[r['global_key_maximum'] for r in trials];exceed=sum(n>=126 for n in maxima)
 report={'schema':'keyed-columnar-post-target-calibration-v1','calibration_plan_sha256':hashlib.sha256((HERE/'calibration-plan.json').read_bytes()).hexdigest(),'timing':'POST-TARGET exploratory; null selected after observing126. No prospective significance claim.','observed_original_per_key_totals_match':True,'observed_maximum':126,'replicates':len(trials),'seed':PLAN['seed'],'null_global_maxima':maxima,'null_min':min(maxima),'null_max':max(maxima),'null_mean':sum(maxima)/len(maxima),'maxima_at_least_observed':exceed,'descriptive_add_one_fraction':(exceed+1)/(len(maxima)+1),'fraction_label':'Post-target descriptive comparison only, not a preregistered discovery p-value.','known_warning_control':positive,'null_trials':trials,'outcome':'Raw-count evidence calibrated exploratorily; whole source claim and general plaintext exclusion remain unsupported.'}
 (HERE/'calibration-results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');original_unchanged();print(json.dumps({k:report[k] for k in ['observed_maximum','replicates','null_min','null_max','null_mean','maxima_at_least_observed','descriptive_add_one_fraction']},indent=2));print('Calibration elapsed seconds (informational):',round(elapsed,3));print('Warning score controls:',positive['true_top_ranked'],'of',positive['score_rank_controls'],'top-ranked; direct hits',positive['direct_dictionary_hits'],'of',positive['word_slots'])
