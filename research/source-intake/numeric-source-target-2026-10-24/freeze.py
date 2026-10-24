import hashlib,json,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];D=ROOT/'experiments/records/numeric-stream-skip-grid';SRC=ROOT.parent/'source-cache/dukotah-cicada3301/liber-primus';CTL=ROOT/'research/source-intake/numeric-skip-controls-2026-10-24'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8',newline='\n')
assert not (D/'frozen-plan.json').exists()
files=['analysis/campaign18_skip/armada/numeric_skip.py','analysis/campaign18_skip/sweep.py','analysis/campaign18_skip/skipdecode.py','analysis/run_stats.py','data/english_quadgrams.txt','data/krisyotam_runes.txt','data/keys/solved_plaintext.txt','data/keys/self_reliance.txt']
files += [p.relative_to(SRC).as_posix() for p in (SRC/'src/lp').glob('*.py')]
for p in files:
 out=D/'source/liber-primus'/p;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SRC/p,out)
shutil.copyfile(SRC.parent/'LICENSE',D/'source/LICENSE')
shutil.copytree(CTL,D/'controls',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
ct=json.loads((CTL/'streams.json').read_text());streams=[x for x in ct if x['branch']=='numeric'];assert len(streams)==33 and all(len(x['key'])==1176 for x in streams);write(D/'streams.json',streams)
sys.path[:0]=[str(SRC/'analysis'),str(SRC/'src')]
from run_stats import load_pages
pages=load_pages()[:-2];ids=[f'lp2-{p:02d}' for p in range(56) if p!=50];assert len(pages)==55
from lp import gematria as gp
for ident,P in zip(ids,pages):assert gp.runes_to_indices(json.loads((ROOT/f'data/pages/{ident}.json').read_text(encoding='utf-8'))['raw'])==P
write(D/'pages.json',[{'id':ident,'indices':list(map(int,P))} for ident,P in zip(ids,pages)])
write(D/'labels.json',gp.IDX_TO_TRANS)
plan={'schema':'numeric-skip-target-v1','frozen_before':'local manuscript target execution','revision':'f08b20b632d91209ddbaa747e8e2f23df0c78ba1','source_branch':'analysis/campaign18_skip/armada/numeric_skip.py --no-fib --full','grid':{'streams':[x['name'] for x in streams],'key_length':1176,'page_ids':ids,'signs':[-1,1],'atbash':[0,1],'offsets':[0,1,2,3,4],'screen_count':36300,'screen_length':50,'screen_width':60,'screen_strict_threshold':-6.5,'confirmation':'Every screen with score > -6.5, complete page, unchanged source beam200; strict full score > -5.5. No confirmation of rejected screens.','max_skip':3},'control_receipt':'controls/CONTROL-RECEIPT.md; full1080outcomes preserved,540 underlying transformed sign/key/offset/reading cases before phase aliases; numeric1subset660cells. Score gate is not exact recovery.','execution':'Source sweep_keystream unchanged; wrap its imported beam to record every screen output and every full survivor; no prefilter, BG/M unused. Source optional Walden excluded and absent.','checks':'Independent Latin scorer re-scores every saved output. Independent scalar beam reconstructs every full survivor and the maximum screen. All source and site page arrays match before target. No global null significance inferred.','quirks':'Historical BBS-labelled constructor includes noncoprime seeds503/311. e uses finite299term source approximation, not exact e beyond digit612. Preserve every labelled phase, not independent hypotheses.','inputs':[{'path':p.relative_to(D).as_posix(),'sha256':sha(p)} for p in sorted(D.rglob('*')) if p.is_file()]}
write(D/'frozen-plan.json',plan);write(Path(__file__).resolve().parent/'target-plan-frozen.json',plan)
print('FROZEN',sha(D/'frozen-plan.json'),'33 streams/55pages/36300screens; no target decoded')
