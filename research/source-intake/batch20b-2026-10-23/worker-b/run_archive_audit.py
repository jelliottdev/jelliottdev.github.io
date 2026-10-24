"""Fresh pinned archive harvest, scorer audit and finite null-bar unit checks."""
import importlib.util,json,sys,hashlib,subprocess,math,collections
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];REPO=ROOT.parent/'source-cache/dukotah-cicada3301';LP=REPO/'liber-primus'
def load(name):
 spec=importlib.util.spec_from_file_location(name,LP/'analysis/round18/L7-redteam'/(name+'.py'));mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
A=load('a1_scorer_language');AA=load('a2_rescore_archive');C=load('c1_bars')
reads=[]
def tracked_open(path,*args,**kwargs):
 p=Path(path);b=p.read_bytes();reads.append({'path':p.resolve().relative_to(REPO.resolve()).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)});return open(path,*args,**kwargs)
AA.open=tracked_open;C.open=tracked_open
candidates,provenance=AA.harvest()
out={'revision':'f08b20b632d91209ddbaa747e8e2f23df0c78ba1','archive_harvest':{'n_candidates':len(candidates),'provenance':provenance,'candidates':candidates},'threshold_scalar_audit':C.c3_gumbel(),'bar_at_N':C.c5_bar_audit(),'tally':C.c6_tally()}
# Source argument exists but does not enter the computation.
assert C.NL.threshold_for(10**9,segment_len=31)==C.NL.threshold_for(10**9,segment_len=400)
out['segment_len_argument_ignored']=True
# independent distribution-free closed-form CDF check of the pure threshold formula,
# not an empirical validation that decoder maxima are Gumbel-distributed.
for n in [2,200,1000000,10**9]:
 bar=C.NL.threshold_for(n,floor=-math.inf)
 cdf=math.exp(-n*math.exp(-(bar-C.NL.DEFAULT_MU)/C.NL.DEFAULT_BETA))
 assert abs(cdf-.99)<1e-12
out['gumbel_formula_unitcheck']='4/4 scalar CDF checks at alpha=.01; validates algebra only.'
# Sweep-level handoff audit: check every retained row, not only first5.
all_row_fields=[]
for meta in provenance:
 if not meta.get('present'):continue
 raw=json.loads((LP/meta['file']).read_text(encoding='utf-8'))
 rows=raw if isinstance(raw,list) else next((raw[key] for key in ['top50','top20','top'] if isinstance(raw.get(key),(list,dict))),[])
 if isinstance(rows,dict):rows=list(rows.values())
 keys=sorted({key for row in rows if isinstance(row,dict) for key in row if any(token in key.lower() for token in ['ioc','lang','lm_','entropy','distinct','agnostic'])})
 all_row_fields.append({'file':meta['file'],'all_retained_rows':len(rows),'candidate_statistic_fields':keys})
out['handoff_all_rows_field_audit']=all_row_fields
# Fresh rescoring of retained strings under four available exact source panel models.
# Missing EN_MODERN/CY models mean this is not the complete six-model source test.
P={}
sp=json.loads((LP/'SOLVED-PAGES.json').read_text(encoding='utf-8'));P['LP1_REAL']=A.sk.eng_to_idx(''.join(p['plaintext_transliteration'] for p in sp['pages']))
la=A._mid(A._read(str(LP/'analysis/latin/latin_218.txt')))+A._mid(A._read(str(LP/'analysis/latin/latin_28233.txt')));P['LATIN']=A.D.text_to_runes(la,'LA').tolist()
oe=A._read(str(LP/'analysis/round10b/B6-non-english-plaintext/corpora/oe_beowulf.txt'));oe='\n'.join(line for line in oe.split('\n') if __import__('re').search('[þðæÞÐÆ]',line));oe+=A._read(str(LP/'data/keys/runepoem_oe.txt'));P['OE']=A.D.text_to_runes(oe,'OE').tolist()
de=A._mid(A._read(str(LP/'analysis/round10b/B6-non-english-plaintext/corpora/de_faust.txt')))+A._mid(A._read(str(LP/'analysis/round10b/B6-non-english-plaintext/corpora/de_2.txt')));P['DE']=A.D.text_to_runes(de,'DE').tolist()
lms={name:AA.D.build_trigram(AA.np.array(value,dtype=AA.np.int64)) for name,value in P.items()}
lengths=sorted({len(A.sk.eng_to_idx(row['text'])) for row in candidates})
nulls=AA.null_table(lms,lengths,n=400)
rescored=[]
for candidate in candidates:
 r=AA.np.array(A.sk.eng_to_idx(candidate['text']),dtype=AA.np.int64);scores={name:AA.score_lm(lm,r) for name,lm in lms.items()}
 rescored.append({'source':candidate['source'],'text':candidate['text'],'n_runes':len(r),'ioc_times29':AA.ioc_n(r),'scores':scores,'uniform_null_z':{name:(value-nulls[(name,len(r))][0])/nulls[(name,len(r))][1] for name,value in scores.items()}})
out['available_model_rescore']={'models':list(lms),'candidate_count':len(rescored),'lengths':lengths,'null_n_per_length':400,'nulls':[{'model':name,'L':L,'mean':v[0],'sd':v[1],'max':v[2]} for (name,L),v in nulls.items()],'rows':rescored,'not_covered':'EN_MODERN andCY models absent. Uniform-rune null z scores are unadjusted exploratory comparisons on English-selected survivors, not proof of recovered plaintext or no missed key.'}
# Record exact data/model/code dependencies for transparent incomplete-panel gate.
required=['data/english_quadgrams.txt','data/krisyotam_runes.txt','data/kjv.txt','SOLVED-PAGES.json','analysis/latin/latin_218.txt','analysis/latin/latin_28233.txt','analysis/round10b/B6-non-english-plaintext/corpora/oe_beowulf.txt','data/keys/runepoem_oe.txt','analysis/round10b/B6-non-english-plaintext/corpora/de_faust.txt','analysis/round10b/B6-non-english-plaintext/corpora/de_2.txt','data/keys/self_reliance.txt']
required+=[str(Path(mod.__file__).resolve().relative_to(LP.resolve())) for mod in [A._score,A.gp,A.sk,A.PL,A.D,C.nc,C.NL]]
for path in sorted(set(required)):
 b=(LP/path).read_bytes();reads.append({'path':'liber-primus/'+path.replace('\\','/'),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
paths=sorted({r['path'] for r in reads});tree={line.split('\t')[1]:line.split()[2] for line in subprocess.check_output(['git','-C',str(REPO),'ls-tree','-r',out['revision'],'--',*paths]).decode().splitlines()}
for row in reads:
 b=(REPO/row['path']).read_bytes();lf=b.replace(b'\r\n',b'\n');oid=lambda x:hashlib.sha1(b'blob '+str(len(x)).encode()+b'\0'+x).hexdigest()
 row['git_object']=tree.get(row['path']);row['relation']='exact' if oid(b)==row['git_object'] else 'CRLF-equivalent' if oid(lf)==row['git_object'] else 'not-pinned'
# The .gitignored model/corpora remain available but must not be mislabeled pinned.
out['inputs']=reads
(HERE/'archive-audit.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print('Harvested',len(candidates),'candidate strings from',sum(p.get('present',False) for p in provenance),'of',len(provenance),'source-listed files.')
print('All-row handoff fields:',all_row_fields)
print('Nonpinned dependency files:',[(r['path'],r['bytes']) for r in reads if r['relation']=='not-pinned'])
print('Tally levels:',{k:v['count'] for k,v in out['tally']['recomputed'].items()})
