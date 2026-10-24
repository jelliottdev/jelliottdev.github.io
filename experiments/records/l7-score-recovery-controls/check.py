"""Independent recovery, score and null-summary checks; --replay also repeats the beam."""
import argparse,hashlib,json,math,statistics,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
TRANS=['F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IA','EA']
def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))
def near(a,b):assert math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-9),(a,b)
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--replay',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
 fixture=read('fixtures.json');result=read('results.json');manifest=read('source-manifest.json')
 for item in manifest['files']:
  path=HERE/Path(item['path']).relative_to('experiments/records/l7-score-recovery-controls');assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
 counts={}
 for line in (HERE/'data/english_quadgrams.txt').read_text().splitlines():
  word,n=line.split();counts[word]=int(n)
 total=sum(counts.values());assert total==7266795
 def score(indices):
  text=''.join(TRANS[i] for i in indices);return sum(math.log10(counts.get(text[i:i+4],.01)/total) for i in range(len(text)-3))/(len(text)-3)
 assert len(fixture['language_plants'])==len(result['language_rows'])==15
 assert len(fixture['mechanism_plants'])==len(result['mechanism_rows'])==28
 for family,result_key in [('language_plants','language_rows'),('mechanism_plants','mechanism_rows')]:
  for plant,row in zip(fixture[family],result[result_key]):
   assert len(plant['plain'])==len(plant['cipher'])==len(row['decoded'])
   assert all(isinstance(n,int) and 0<=n<29 for n in plant['plain']+plant['cipher']+row['decoded'])
   recovery=sum(a==b for a,b in zip(plant['plain'],row['decoded']))/len(plant['plain']);near(recovery,row['recovery']);near(score(row['decoded']),row['score'])
   if family=='language_plants':near(score(row['wrong_decoded']),row['wrong_key_score'])
   else:assert row['passes_score']==(row['score']>=-5.5) and row['recovers_90pct']==(recovery>=.9)
 for row in result['nulls']:
  values=row['values'];assert len(values)==row['n']==120
  near(sum(values)/len(values),row['mean']);near(max(values),row['max']);ordered=sorted(values);threshold=ordered[108];excess=[v-threshold for v in ordered if v>threshold]
  assert len(excess)==row['tail_exceedances']==11
  near(sum(excess)/len(excess),row['tail_beta']);near(row['tail_beta']/.0725,row['beta_ratio_to_source_default'])
 bad=sum(row['score']>=-5.5 and row['recovery']<.9 for row in result['mechanism_rows']);assert bad==result['score_pass_below_90pct']==4
 for summary in result['mechanism_summary']:
  rows=[row for row in result['mechanism_rows'] if row['case']==summary['case']];assert len(rows)==summary['n']==7
  near(statistics.median(row['score'] for row in rows),summary['median_score']);near(statistics.median(row['recovery'] for row in rows),summary['median_recovery'])
  assert sum(row['passes_score'] for row in rows)==summary['passes_score']
 for summary in result['language_summary']:
  rows=[row for row in result['language_rows'] if row['register']==summary['register']];assert len(rows)==summary['n']==3
  near(statistics.median(row['score'] for row in rows),summary['median_score'])
 if args.replay:subprocess.run([sys.executable,str(HERE/'run.py'),'--check'],check=True)
 print('Independent count, rune recovery, English score and null-tail summaries agree; four score passes recover under 90%.')
if __name__=='__main__':main()
