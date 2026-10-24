"""Fixed literal GP29 marker census; no URL or language inference."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PLAN=json.loads((HERE/'plan.json').read_bytes());HASHES={x['path']:x['sha256'] for x in PLAN['inputs']}
def source(p):
 raw=(ROOT/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==HASHES[p],p;return json.loads(raw)
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
def locate(values,pattern):
 # Sliding arithmetic-index windows, overlapping starts included.
 size=len(pattern)
 return [i for i in range(len(values)-size+1) if all(values[i+j]==p for j,p in enumerate(pattern))]
def main():
 alphabet=source('data/index.json')['alphabet'];assert len(alphabet)==29
 labels=[x['latin'] for x in alphabet];lookup={x['rune']:i for i,x in enumerate(alphabet)}
 one={s:i for i,s in enumerate(labels) if len(s)==1};tokens={t:[one[c] for c in t] for t in PLAN['tokens']}
 control_count=0
 for a in PLAN['map_grid']['a']:
  inv=pow(a,-1,29)
  for b in PLAN['map_grid']['b']:
   for token,pattern in tokens.items():
    plain=PLAN['control']['plain_prefix']+pattern+PLAN['control']['plain_suffix']
    cipher=[inv*(v-b)%29 for v in plain];decoded=[(a*c+b)%29 for c in cipher]
    assert decoded==plain and PLAN['control']['fixed_start'] in locate(decoded,pattern),(a,b,token)
    control_count+=1
 assert control_count==3248
 matches=[];pages=[];triple_rows=[];counts={t:0 for t in tokens};starts={t:0 for t in tokens}
 for pid in PLAN['pages']:
  page=source(f'data/pages/{pid}.json');cipher=[];locations=[]
  for li,line in enumerate(page['lines']):
   for col,rune in enumerate(line['raw']):
    if rune in lookup:cipher.append(lookup[rune]);locations.append([li,col])
  assert len(cipher)==page['rune_count'],pid
  triples=[i for i in range(len(cipher)-2) if cipher[i]==cipher[i+1]==cipher[i+2]]
  triple_rows += [{'page':pid,'rune_start_zero_based':i,'cipher_index':cipher[i]} for i in triples]
  pages.append({'page':pid,'runes':len(cipher),'equal_symbol_triples':len(triples),'removed_nonrune_characters':sum(len(l['raw']) for l in page['lines'])-len(cipher)})
  for t,p in tokens.items():starts[t]+=max(0,len(cipher)-len(p)+1)
  for a in PLAN['map_grid']['a']:
   for b in PLAN['map_grid']['b']:
    plain=[(a*c+b)%29 for c in cipher]
    for token,pattern in tokens.items():
     for start in locate(plain,pattern):
      end=start+len(pattern);lo=max(0,start-PLAN['snippet_flank_runes']);hi=min(len(cipher),end+PLAN['snippet_flank_runes'])
      matches.append({'page':pid,'token':token,'a':a,'b':b,'rune_start_zero_based':start,'rune_end_exclusive':end,'cipher_indices':cipher[start:end],'plain_indices':plain[start:end],'source_line_columns_zero_based':locations[start:end],'snippet_rune_start':lo,'snippet_indices':plain[lo:hi],'snippet_rune_labels':[labels[v] for v in plain[lo:hi]],'snippet_marked':' '.join(labels[v] for v in plain[lo:start])+' ['+token+'] '+' '.join(labels[v] for v in plain[end:hi])})
      counts[token]+=1
 matches.sort(key=lambda r:(r['page'],r['a'],r['b'],r['token'],r['rune_start_zero_based']))
 write(HERE/'matches.json',matches)
 results={'schema':'url-marker-affine-census-result-v1','plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),'input_hashes_verified':len(HASHES),'map_count':812,'page_count':len(pages),'nonempty_pages':sum(p['runes']>0 for p in pages),'empty_pages':[p['page'] for p in pages if not p['runes']],'total_runes':sum(p['runes'] for p in pages),'nonempty_page_map_outputs':812*sum(p['runes']>0 for p in pages),'tokens':tokens,'candidate_rune_starts_per_token_per_map':starts,'literal_matches_by_token':counts,'total_literal_matches':len(matches),'distinct_page_map_start_positions':len({(r['page'],r['a'],r['b'],r['rune_start_zero_based']) for r in matches}),'overlap_note':'HTTP is a prefix of HTTPS; matches sharing page/map/start are not independent candidate locations.','distinct_matched_page_start_windows':{t:len({(r['page'],r['rune_start_zero_based']) for r in matches if r['token']==t}) for t in tokens},'pages_with_matches':{t:len({r['page'] for r in matches if r['token']==t}) for t in tokens},'plant_controls':{'map_token_cases':control_count,'passed':True,'fixed_offset':8},'original_equal_symbol_triples':triple_rows,'pages':pages,'interpretation':'Literal marker compatibility under fixed affine maps only. Matches are not URLs; no punctuation/hostname grammar, language scoring or probability test.','matches_sha256':hashlib.sha256((HERE/'matches.json').read_bytes()).hexdigest()}
 write(HERE/'results.json',results)
 print(json.dumps({k:results[k] for k in ['nonempty_pages','empty_pages','total_runes','literal_matches_by_token','total_literal_matches','distinct_matched_page_start_windows','pages_with_matches','plant_controls']},indent=2))
if __name__=='__main__':main()
