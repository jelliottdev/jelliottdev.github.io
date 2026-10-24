"""Replay finite known-plaintext and conditional-null controls using unchanged source beam."""
import argparse,hashlib,json,math,random,statistics,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'vendor'))
import skipdecode as sk

def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))
def clean(value):
 if isinstance(value,float):return round(value,10)
 if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
 if isinstance(value,list):return [clean(v) for v in value]
 return value

def calculate():
 fixture=read('fixtures.json');assert fixture['schema']=='liberpedia-l7-finite-fixtures-v1'
 keys={name:list(bytes.fromhex(value)) for name,value in fixture['keys'].items()}
 decode=lambda ct,key,width=400:sk.beam_decode(ct,key,sign=-1,o=0,beam_w=width,max_skip=3)
 languages=[];mechanisms=[];nulls=[]
 for row in fixture['language_plants']:
  actual=decode(row['cipher'],keys[row['key']]);wrong=decode(row['cipher'],[(i*7+13)%29 for i in range(len(keys[row['key']]))])
  languages.append({'register':row['register'],'rep':row['rep'],'score':actual['score'],'recovery':sum(a==b for a,b in zip(actual['plain_idx'],row['plain']))/len(row['plain']),'decoded':actual['plain_idx'],'wrong_key_score':wrong['score'],'wrong_decoded':wrong['plain_idx']})
 for row in fixture['mechanism_plants']:
  actual=decode(row['cipher'],keys[row['key']]);recovery=sum(a==b for a,b in zip(actual['plain_idx'],row['plain']))/len(row['plain'])
  mechanisms.append({'case':row['case'],'seed':row['seed'],'score':actual['score'],'recovery':recovery,'decoded':actual['plain_idx'],'passes_score':actual['score']>=-5.5,'recovers_90pct':recovery>=.9})
 for setting in fixture['null_settings']:
  values=[]
  for rep in range(setting['n']):
   ct=fixture['null_prefix'][:setting['L']];random.Random(setting['shuffle_seed0']+rep).shuffle(ct)
   values.append(decode(ct,keys[setting['key']],setting['beam_w'])['score'])
  ordered=sorted(values);threshold=ordered[int(.9*len(ordered))];excess=[v-threshold for v in ordered if v>threshold];beta=statistics.mean(excess)
  nulls.append({**setting,'values':values,'mean':statistics.mean(values),'max':max(values),'tail_threshold':threshold,'tail_exceedances':len(excess),'tail_beta':beta,'beta_ratio_to_source_default':beta/.0725})
 language_summary=[{'register':name,'median_score':statistics.median(r['score'] for r in languages if r['register']==name),'median_recovery':statistics.median(r['recovery'] for r in languages if r['register']==name),'n':3} for name in read('plan.json')['language_controls']['registers']]
 mechanism_summary=[{'case':name,'n':7,'median_score':statistics.median(r['score'] for r in mechanisms if r['case']==name),'median_recovery':statistics.median(r['recovery'] for r in mechanisms if r['case']==name),'passes_score':sum(r['passes_score'] for r in mechanisms if r['case']==name),'passes_score_below_90pct':sum(r['passes_score'] and not r['recovers_90pct'] for r in mechanisms if r['case']==name)} for name in read('plan.json')['mechanism_controls']['cases']]
 return clean({'schema':'liberpedia-l7-finite-control-results-v1','source_revision':fixture['source_revision'],'language_rows':languages,'mechanism_rows':mechanisms,'language_summary':language_summary,'mechanism_summary':mechanism_summary,'nulls':nulls,'score_pass_below_90pct':sum(r['passes_score'] and not r['recovers_90pct'] for r in mechanisms)})

def main():
 args=argparse.ArgumentParser(description=__doc__);args.add_argument('--check',action='store_true');options=args.parse_args()
 result=calculate();raw=(json.dumps(result,indent=2)+'\n').encode()
 if options.check:assert (HERE/'results.json').read_bytes()==raw,'Result replay mismatch'
 else:(HERE/'results.json').write_bytes(raw)
 print('Checked 15 paired language plants, 28 mechanism plants and 360 conditional nulls;',result['score_pass_below_90pct'],'score passes recover under 90%.')
if __name__=='__main__':main()
