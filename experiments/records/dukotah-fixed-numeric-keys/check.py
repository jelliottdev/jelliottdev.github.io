"""Independent scalar check of every Campaign VII fixed numeric-key setting."""
from __future__ import annotations
import pathlib,hashlib,json,math,csv,re
root=pathlib.Path(__file__).resolve().parent
source=root/'source'
site=root.parents[2]
RUNES='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
LABELS=('F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IA','EA')
HEX=('36367763ab73783c7af284446c59466b4cd653239a311cb7116d4618dee09a84'
     '25893dc7500b464fdaf1672d7bef5e891c6e2274568926a49fb4f45132c2a8b4')
hb=bytes.fromhex(HEX)
printed=json.loads((site/'data/pages/lp2-56.json').read_text(encoding='utf-8'))
printed_rows=[line['raw'].strip('/') for line in printed['lines']
              if re.fullmatch(r'[0-9a-f]+/',line['raw'])]
assert len(printed_rows)==5 and ''.join(printed_rows)==HEX
def chain(fn,need):
 out=[];cur=hb
 while len(out)<need:
  cur=fn(cur).digest();out.extend(cur)
 return out[:need]
def branches(need):
 mayan=[10,2,14,7,19,6,18,12,7,8,17,0,19]
 out=[('B1','mayan_fwd',mayan),('B1','mayan_rev',mayan[::-1])]
 out += [('B4','hash_bytes',[x%29 for x in hb]),('B4','hash_hexdigits',[int(c,16)%29 for c in HEX]),('B4','shake256',[x%29 for x in hashlib.shake_256(hb).digest(need)]),('B4','sha512_chain',[x%29 for x in chain(hashlib.sha512,need)]),('B4','blake2b_chain',[x%29 for x in chain(hashlib.blake2b,need)])]
 c2=[('cuneiform_17_13_55_1',[17,13,55,1]),('cuneiform_rev',[1,55,13,17]),('digits_1033',[1,0,3,3]),('digits_3301',[3,3,0,1]),('cuneiform+1033+3301',[17,13,55,1,1,0,3,3,3,3,0,1])]
 out += [('C2',name,[x%29 for x in values]) for name,values in c2]
 assert len(out)==12
 return out
def model():
 counts={}
 for line in (source/'data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
  quad,count=line.split();counts[quad]=int(count)
 total=sum(counts.values());logtotal=math.log10(total)
 return {quad:math.log10(count)-logtotal for quad,count in counts.items()},math.log10(.01)-logtotal
def score(path,M,floor):
 text=''.join(LABELS[x] for x in path)
 if len(text)<4:return -999.0
 return sum(M.get(text[i:i+4],floor) for i in range(len(text)-3))/(len(text)-3)
def pages():
 raw=(source/'data/krisyotam_runes.txt').read_text(encoding='utf-8')
 allpages=[[RUNES.index(ch) for ch in s if ch in RUNES] for s in raw.split('%')]
 allpages=[p for p in allpages if p]
 assert len(allpages)==57
 p=allpages[:-2];ids=[f'lp2-{n:02d}' for n in range(56) if n!=50]
 for id,page in zip(ids,p):
  sitepage=json.loads((site/'data/pages'/(id+'.json')).read_text(encoding='utf-8'))
  assert page==[RUNES.index(ch) for ch in sitepage['raw'] if ch in RUNES]
 assert len(p)==len(ids)==55 and sum(map(len,p))==12956
 return list(zip(ids,p))+[('WHOLE',[x for page in p for x in page])]
def decrypt(ct,key,sign,atb,interrupter):
 out=[];phase=0
 for c in ct:
  if interrupter and c==0:out.append(0);continue
  x=28-c if atb else c
  out.append((x+sign*key[phase%len(key)])%29);phase+=1
 return out
def known(n):
 r=list(csv.DictReader((site/'exports/readings'/(n+'.csv')).open(encoding='utf-8-sig',newline='')))
 return [int(x['output_index']) for x in r]
def plant(P,key,sign,atb,interrupter):
 ct=[];expected=[];phase=0;forced=0
 for p in P:
  if interrupter and p==0:
   ct.append(0);expected.append(0);continue
  pre=(p-sign*key[phase%len(key)])%29
  stored=28-pre if atb else pre
  if interrupter and stored==0:
   ct.append(0);expected.append(0);forced+=1;continue
  ct.append(stored);expected.append(p);phase+=1
 return ct,expected,forced
M,floor=model();targets=pages();keys=branches(12956+8);rows=[]
for branch,name,key in keys:
 for target,ct in targets:
  for sign in (-1,1):
   for atb in (False,True):
    for INT in (False,True):
     p=decrypt(ct,key,sign,atb,INT);s=score(p,M,floor)
     rows.append(dict(branch=branch,key=name,target=target,sign=sign,atbash=int(atb),interrupter=int(INT),runes=len(ct),score=s,plaintext_sha256=hashlib.sha256(bytes(p)).hexdigest(),plaintext_prefix=''.join(LABELS[x] for x in p)[:80] if target!='WHOLE' else ''))
assert len(rows)==5376
reading85=known('lp2-56');reading184=known('warning');samples=[('lp2-56',reading85),('warning',reading184),('repeat-277',(reading85*4)[:277])]
controls=[]
for branch,name,key in keys:
 for sign in (-1,1):
  for atb in (False,True):
   for INT in (False,True):
    for sample,P in samples:
     ct,expected,forced=plant(P,key,sign,atb,INT)
     got=decrypt(ct,key,sign,atb,INT);assert got==expected
     controls.append(dict(branch=branch,key=name,sign=sign,atbash=int(atb),interrupter=int(INT),sample=sample,runes=len(P),forced_literal_F=forced,complete_expected_match=len(got)==len(expected) and got==expected,unchanged_known_runes=sum(a==b for a,b in zip(got,P)),score=score(got,M,floor),above_source_bar=score(got,M,floor)>-5.2))
assert len(controls)==288
bybranch={}
for branch in ('B1','B4','C2'):
 rr=[r for r in rows if r['branch']==branch];w=max(rr,key=lambda x:x['score']);bybranch[branch]={'settings':len(rr),'best':w,'hits':sum(x['score']>-5.2 for x in rr)}
source_reports={b:json.loads((source/'analysis/campaign7'/n).read_text(encoding='utf-8')) for b,n in [('B1','b1_mayan_results.json'),('B4','b4_hash_kdf_results.json'),('C2','c2_cuneiform_results.json')]}
for b,s in bybranch.items():
 report=source_reports[b]; assert round(s['best']['score'],3)==report['best_score']; assert s['hits']==report['n_hits']==0
 assert s['best']['key']==report['best']['key']; expected_target='WHOLE' if report['best']['target']=='WHOLE' else targets[int(report['best']['target'][1:])][0]; assert s['best']['target']==expected_target
actual={'schema':'liberpedia-campaign7-fixedkeys-receipt-v1','source_revision':'f08b20b632d91209ddbaa747e8e2f23df0c78ba1','plan_sha256':hashlib.sha256((root/'plan-frozen.json').read_bytes()).hexdigest(),'target_count':len(targets),'source_site_rune_matches':55,'case_count':len(rows),'control_count':len(controls),'source_bar':-5.2,'by_branch':bybranch,'control_power':{'noint_above':sum(c['above_source_bar'] for c in controls if c['interrupter']==0),'noint_total':144,'int_above':sum(c['above_source_bar'] for c in controls if c['interrupter']==1),'int_total':144,'all_exact_constructed':all(c['complete_expected_match'] for c in controls)},'source_reports':source_reports,'rows':rows,'controls':controls}
assert actual['control_power']['noint_above']==144 and actual['control_power']['int_above']==141
saved=json.loads((root/'results.json').read_text(encoding='utf-8'))
assert actual==saved, 'Full source-grid or planted-control ledger differs'
plan=json.loads((root/'plan-frozen.json').read_text(encoding='utf-8'))
for name,digest in plan['source_files_sha256'].items():
 assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest,name
for name,digest in plan['known_reading_sha256'].items():
 assert hashlib.sha256((site/'exports/readings'/(name+'.csv')).read_bytes()).hexdigest()==digest,name
print('PASS: 5,376 complete scores and path hashes; 288 planted controls; 55 source/site pages')
print('Source bar: 0 manuscript hits; plants above bar: 144/144 no-F and 141/144 F-null')


