"""Independent complete decoded-stream substring census and output-field checker."""
import hashlib,json,re
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
plan=json.loads((HERE/'plan.json').read_bytes())
for row in plan['inputs']:assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256']
alphabet=json.loads((ROOT/'data/index.json').read_bytes())['alphabet'];labels=[x['latin'] for x in alphabet];rune_to_char={x['rune']:chr(65+i) for i,x in enumerate(alphabet)}
tokenchars={t:''.join(chr(65+labels.index(c)) for c in t) for t in plan['tokens']}
matched=[];triples=[];checked_outputs=0;zero_pages=[];by_page={}
for pid in plan['pages']:
 page=json.loads((ROOT/f'data/pages/{pid}.json').read_bytes())
 # Build one-codepoint-per-rune source independently from complete raw lines.
 raw=''.join(l['raw'] for l in page['lines']);cipher=''.join(rune_to_char.get(c,'') for c in raw)
 assert len(cipher)==page['rune_count']
 by_page[pid]=cipher
 if not cipher:zero_pages.append(pid)
 triples += [(pid,m.start()) for m in re.finditer(r'(?=(.)\1\1)',cipher)]
 for a in range(1,29):
  for b in range(29):
   table=str.maketrans({chr(65+i):chr(65+(i*a+b)%29) for i in range(29)})
   decoded=cipher.translate(table);checked_outputs+=1
   for token,needle in tokenchars.items():
    offset=decoded.find(needle)
    while offset!=-1:
     matched.append((pid,a,b,token,offset));offset=decoded.find(needle,offset+1)
actual=json.loads((HERE/'matches.json').read_bytes());keys=[(r['page'],r['a'],r['b'],r['token'],r['rune_start_zero_based']) for r in actual]
assert len(set(keys))==len(keys) and sorted(keys)==sorted(matched)
for row in actual:
 pid,a,b,token,start=row['page'],row['a'],row['b'],row['token'],row['rune_start_zero_based'];cipher=[ord(c)-65 for c in by_page[pid]]
 decoded=[(a*i+b)%29 for i in cipher];end=start+len(token);lo=max(0,start-8);hi=min(len(cipher),end+8)
 assert row['cipher_indices']==cipher[start:end] and row['plain_indices']==[labels.index(c) for c in token]
 assert row['rune_end_exclusive']==end and row['snippet_rune_start']==lo and row['snippet_indices']==decoded[lo:hi]
 assert row['snippet_rune_labels']==[labels[v] for v in decoded[lo:hi]]
 expected=' '.join(labels[v] for v in decoded[lo:start])+' ['+token+'] '+' '.join(labels[v] for v in decoded[end:hi])
 assert row['snippet_marked']==expected
 source=json.loads((ROOT/f'data/pages/{pid}.json').read_bytes());loc=[(li,col) for li,l in enumerate(source['lines']) for col,c in enumerate(l['raw']) if c in rune_to_char]
 assert row['source_line_columns_zero_based']==[list(x) for x in loc[start:end]]
# Independent planted encipherments: one-codepoint-string translations rather than source scanner.
plants=0
for a in range(1,29):
 for b in range(29):
  inverse=pow(a,27,29)
  for token,needle in tokenchars.items():
   p=''.join(chr(65+i) for i in plan['control']['plain_prefix'])+needle+''.join(chr(65+i) for i in plan['control']['plain_suffix'])
   cipher=p.translate(str.maketrans({chr(65+i):chr(65+inverse*(i-b)%29) for i in range(29)}))
   decoded=cipher.translate(str.maketrans({chr(65+i):chr(65+(i*a+b)%29) for i in range(29)}))
   assert decoded==p and decoded.find(needle,8)==8;plants+=1
results=json.loads((HERE/'results.json').read_bytes());counts=dict(Counter(k[3] for k in matched))
assert all(results['literal_matches_by_token'][t]==counts.get(t,0) for t in plan['tokens'])
assert results['matches_sha256']==hashlib.sha256((HERE/'matches.json').read_bytes()).hexdigest()
assert results['distinct_page_map_start_positions']==len({k[:3]+k[4:] for k in matched})
assert zero_pages==['lp2-50'];assert plants==3248
receipt={'plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),'complete_decoded_streams_checked':checked_outputs,'nonempty_decoded_streams':checked_outputs-812*len(zero_pages),'all_match_tuples_and_fields_agree':True,'total_literal_matches':len(matched),'counts':{t:counts.get(t,0) for t in plan['tokens']},'independent_planted_map_token_cases':plants,'original_equal_symbol_triples':triples,'WWW_bijective_invariant':'For any injective symbol map f, f(c0)=f(c1)=f(c2)=W requires c0=c1=c2. Therefore absence of equal-symbol triples rules out literal WWW under every static bijective substitution, not just affine maps. This does not exclude URLs without WWW or changing-key layers.','all_checks_passed':True}
(HERE/'independent-check.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print(json.dumps(receipt,indent=2))
