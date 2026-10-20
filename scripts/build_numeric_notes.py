"""Rebuild mathematical reference notes from the shipped rune records."""
from pathlib import Path
import json,re,math,hashlib
root=Path(globals().get('OUTPUT_ROOT',Path(__file__).resolve().parents[1]))
def read(path):return json.loads((root/path).read_text(encoding='utf-8'))
alphabet=read('data/index.json')['alphabet']; by={x['rune']:x for x in alphabet}
known=read('data/evidence/known-readings.json')
def prime(n):return n>1 and all(n%d for d in range(2,math.isqrt(n)+1))
def record(runes):
 tokens=[by[ch] for ch in runes if ch in by];n=sum(t['prime'] for t in tokens);rev=int(str(n)[::-1]);return {'runes':''.join(t['rune'] for t in tokens),'labels':[t['latin'] for t in tokens],'values':[t['prime'] for t in tokens],'sum':n,'prime':prime(n),'reverse':rev,'reverse_prime':prime(rev),'emirp':prime(n) and prime(rev) and n!=rev}
words=[];clauses=[]
for control in known['controls']:
 for d in control['decoded_pages']:
  p=read(f'data/pages/{d["page"]}.json');it=iter(d['rune_indices']);decoded=''.join(alphabet[next(it)]['rune'] if c in by else c for c in p['raw'])
  joined=decoded.replace('/\n','').replace('/','').replace('\n','')
  for ordinal,w in enumerate(re.findall('[%s]+'%''.join(by),joined)):
   v=record(w);label=''.join(v['labels'])
   if label in ['WIDSOM','WISDOM','BELIEUE','CWESTIAN','FUNCTIAN','ILLUSIANS','SUFFERNG']:
    words.append(dict(v,page=p['id'],word_ordinal=ordinal,image_sha256=p['image_sha256']))
  if p['id']=='lp2-57':
   for part in joined.split('.'):
    v=record(part)
    if v['runes']:clauses.append(dict(v,literal=''.join(by[c]['latin'] if c in by else c for c in part),page=p['id']))
result={'schema':'wiki-spelling-sums-v1','scope':'Rune-only additive GP sums from the shipped known readings. Decoded rune indices preserve the documented LP1-10 correction. Not a new full image audit.','conventions':{'counted':'Each rune contributes its Gematria Primus prime value once.','excluded':'Punctuation, spaces, line markers, and decimal digits.','segmentation':'Remove archive line-wrap markers; separate words at non-runes and LP2-57 clauses at archived periods.','primality':'Exact trial division through floor(sqrt(n)); decimal reversal for emirps.'},'source_sha256':{'known_readings':hashlib.sha256((root/'data/evidence/known-readings.json').read_bytes()).hexdigest()},'words':words,'lp2_57_clauses':clauses}
assert [x['sum'] for x in clauses]==[449,1259,1031,1229]
assert all(x['emirp'] for x in clauses[1:])
assert next(x['sum'] for x in words if ''.join(x['labels'])=='CWESTIAN')==347
(root/'data/evidence/spelling-sums.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Verified',len(words),'word occurrences and four LP2-57 text segments')
