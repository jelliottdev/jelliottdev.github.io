"""Materialize compact exact-source finite controls, not full source corpora."""
import importlib.util,json,sys,random,re,hashlib,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];LP=ROOT.parent/'source-cache/dukotah-cicada3301/liber-primus';OUT=ROOT/'experiments/records/l7-score-recovery-controls'
OUT.mkdir(parents=True,exist_ok=True);(OUT/'vendor/lp').mkdir(parents=True,exist_ok=True);(OUT/'data').mkdir(exist_ok=True)
def load(name):
 spec=importlib.util.spec_from_file_location(name,LP/'analysis/round18/L7-redteam'/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
A=load('a1_scorer_language');B=load('b1_power_envelope');C=load('c1_bars')
P={};P['EN_KJV']=A.D.text_to_runes(A._mid(A._read(str(LP/'data/kjv.txt')))[:900000],'EN').tolist()
sp=json.loads((LP/'SOLVED-PAGES.json').read_text(encoding='utf-8'));P['LP1_REAL']=A.sk.eng_to_idx(''.join(p['plaintext_transliteration'] for p in sp['pages']))
la=A._mid(A._read(str(LP/'analysis/latin/latin_218.txt')))+A._mid(A._read(str(LP/'analysis/latin/latin_28233.txt')));P['LATIN']=A.D.text_to_runes(la,'LA').tolist()
oe=A._read(str(LP/'analysis/round10b/B6-non-english-plaintext/corpora/oe_beowulf.txt'));oe='\n'.join(line for line in oe.split('\n') if re.search('[þðæÞÐÆ]',line));oe+=A._read(str(LP/'data/keys/runepoem_oe.txt'));P['OE']=A.D.text_to_runes(oe,'OE').tolist()
de=A._mid(A._read(str(LP/'analysis/round10b/B6-non-english-plaintext/corpora/de_faust.txt')))+A._mid(A._read(str(LP/'analysis/round10b/B6-non-english-plaintext/corpora/de_2.txt')));P['DE']=A.D.text_to_runes(de,'DE').tolist()
fixtures={'schema':'liberpedia-l7-finite-fixtures-v1','source_revision':'f08b20b632d91209ddbaa747e8e2f23df0c78ba1','keys':{},'language_plants':[],'mechanism_plants':[],'null_prefix':C.nc.unsolved()[:400],'null_settings':[]}
fixtures['keys']['a1']=bytes(A.PL.make_key('sha256_ctr',length=992,seed=b'CICADA3301')).hex()
fixtures['keys']['b1']=bytes(B.key_sha(4624)).hex()
for name,idx in P.items():
 for rep in range(3):
  rng=random.Random(A.SEED0+rep*977+120);offset=rng.randrange(0,len(idx)-121);plain=idx[offset:offset+120];key=list(bytes.fromhex(fixtures['keys']['a1']));ct,skips,_=A.sk.encipher_keyskip(plain,key,sign=-1,supp=.83,seed=A.SEED0+rep)
  fixtures['language_plants'].append({'register':name,'rep':rep,'source_plain_offset':offset,'plain':plain,'cipher':ct,'key':'a1','n_skips':int(sum(skips))})
for name,mech,params in [('baseline','keyskip',{'supp':.83}),('paired rejection','skip_by_two',{'supp':.83}),('one free advance','drift_at',{'supp':.83,'ndrift':1}),('free advance q=.02','free_drift',{'supp':.83,'q':.02})]:
 for seed in range(7):
  plain=B.take_plain(240,seed);ct,info=B.MECH[mech](plain,list(bytes.fromhex(fixtures['keys']['b1'])),seed=3301+seed,**params)
  fixtures['mechanism_plants'].append({'case':name,'mechanism':mech,'params':params,'seed':seed,'plain':plain,'cipher':ct,'key':'b1','generation_info':info})
for length,beam in [(31,120),(120,400),(400,120)]:
 key='null'+str(length);fixtures['keys'][key]=bytes(A.PL.make_key('sha256_ctr',length=length*5+4096,seed=b'L7-NULL-PAD')).hex();fixtures['null_settings'].append({'L':length,'beam_w':beam,'n':120,'key':key,'shuffle_seed0':70000})
(OUT/'fixtures.json').write_text(json.dumps(fixtures,separators=(',',':'))+'\n',encoding='utf-8')
files={'src/lp/gematria.py':'vendor/lp/gematria.py','src/lp/score.py':'vendor/lp/score.py','analysis/campaign18_skip/skipdecode.py':'vendor/skipdecode.py','data/english_quadgrams.txt':'data/english_quadgrams.txt'}
manifest=[]
for source,target in files.items():
 raw=(LP/source).read_bytes();(OUT/target).write_bytes(raw);manifest.append({'source_path':'liber-primus/'+source,'path':'experiments/records/l7-score-recovery-controls/'+target,'sha256':hashlib.sha256(raw).hexdigest()})
(OUT/'vendor/lp/__init__.py').write_text('# Local package for three unchanged source modules.\n',encoding='utf-8')
(OUT/'source-manifest.json').write_text(json.dumps({'source_revision':fixtures['source_revision'],'files':manifest,'note':'Vendor module bytes unchanged. Minimal package wrapper and recorded rune/key fixtures make the finite replay independent of the larger checkout.'},indent=2)+'\n',encoding='utf-8')
print('Materialized',len(fixtures['language_plants']),'language plants,',len(fixtures['mechanism_plants']),'mechanism plants and360 deterministic nulls.')
