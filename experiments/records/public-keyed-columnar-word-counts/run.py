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
source=HERE/'source-keyed-columnar.py'
tree=ast.parse(source.read_text());chosen=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['get_column_order','columnar_transpose_decrypt']];assert len(chosen)==2
namespace={};exec(compile(ast.Module(body=chosen,type_ignores=[]),str(source),'exec'),namespace)
dec=namespace['columnar_transpose_decrypt'];order=namespace['get_column_order']
def enc_column(values,key):return [values[i] for col in sorted(range(len(key)),key=lambda c:(key[c],c)) for i in range(col,len(values),len(key))]
# Independent inverse via position-permutation ranks rather than a ragged row grid.
def indep_column(values,key):
 positions=sorted(range(len(values)),key=lambda i:(key[i%len(key)],i%len(key),i//len(key)))
 out=[None]*len(values)
 for j,i in enumerate(positions):out[i]=values[j]
 return out
controls=0;maxlen=max(map(len,plan['keyed_columnar']['clean_keywords']))
for key in plan['keyed_columnar']['clean_keywords']:
 for n in range(2*maxlen+4):
  p=list(range(n));c=enc_column(p,key);assert dec(c,key)==p and indep_column(c,key)==p;controls+=1
 c=enc_column(plain64,key);assert dec(c,key)==plain64 and indep_column(c,key)==plain64;controls+=1
lexicon={w.upper() for w in (ROOT/'experiments/records/rail-fence-visible-words/lexicon.txt').read_text(encoding='ascii').splitlines() if len(w)>=3}
# Source transcription rule: slash/newline removed; hyphens only delimit words.
pages=[]
for pid in plan['pages']:
 page=json.loads((ROOT/f'data/pages/{pid}.json').read_bytes());raw=''.join(l['raw'] for l in page['lines']).replace('/','');words=[[lookup[c] for c in w if c in lookup] for w in raw.split('-')];words=[w for w in words if w];cipher=[v for w in words for v in w];assert len(cipher)==page['rune_count'];pages.append((pid,cipher,[len(w) for w in words]))
def score(vals,lengths):
 i=hits=0
 for n in lengths:
  word=''.join(labels[v] for v in vals[i:i+n]);hits+=word in lexicon;i+=n
 assert i==len(vals)
 return hits
column_rows=[];totals=[]
for keyword,key in zip(plan['keyed_columnar']['source_keywords'],plan['keyed_columnar']['clean_keywords']):
 total=0
 for pid,cipher,lengths in pages:
  out=dec(cipher,key);assert out==indep_column(cipher,key)
  hits=score(out,lengths);total+=hits
  column_rows.append({'page':pid,'source_keyword':keyword,'clean_keyword':key,'hits':hits,'visible_slots':len(lengths),'decoded_indices_sha256':hashlib.sha256(bytes(out)).hexdigest()})
 totals.append({'source_keyword':keyword,'clean_keyword':key,'hits':total})
write(HERE/'cases.json',column_rows)
write(HERE/'results.json',{'plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),'source_helpers':'Only two statically inspected source function definitions compiled; no module top-level/network code executed.','controls_passed':controls,'independent_all_target_permutations_agree':True,'source_keywords':len(totals),'effective_column_order_specs':len({(len(k),tuple(order(k))) for k in plan['keyed_columnar']['clean_keywords']}),'page_key_cases':len(column_rows),'nonempty_page_key_cases':sum(bool(c) for _,c,_ in pages)*len(totals),'lexicon_entries':len(lexicon),'visible_word_slots':sum(len(l) for _,_,l in pages),'runes':sum(len(c) for _,c,_ in pages),'per_keyword_totals':totals,'maximum_raw_hits':max(r['hits'] for r in totals),'best_keywords':[r['source_keyword'] for r in totals if r['hits']==max(t['hits'] for t in totals)],'outcome':'inconclusive','limit':'Raw fixed-dictionary counts only, with no calibrated success/null criterion. Neither exact archival input replay nor a no-English-solve assertion.'})

print(json.dumps({'columnar_controls':controls,'max_raw_hits':max(r['hits'] for r in totals),'outcome':'inconclusive'},indent=2))
