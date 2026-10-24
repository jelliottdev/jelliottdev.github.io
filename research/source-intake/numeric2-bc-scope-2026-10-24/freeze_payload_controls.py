import hashlib,json,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];D=ROOT/'experiments/records/payload-phase-skip-grid';SRC=ROOT.parent/'source-cache/dukotah-cicada3301/liber-primus';PREV=ROOT/'experiments/records/numeric-stream-skip-grid'
assert not (D/'control-plan.json').exists()
shutil.copytree(PREV/'source',D/'source',ignore=shutil.ignore_patterns('__pycache__','*.pyc'),dirs_exist_ok=True)
for relative in ['analysis/campaign18_skip/armada2/numeric2_skip.py','analysis/pp49_51/canon_256.bin','analysis/pp49_51/canon_256_decpref.bin']:
 p=D/'source/liber-primus'/relative;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SRC/relative,p)
for file,original in [('known-readings.json',PREV/'controls/known-readings.json'),('pages.json',PREV/'pages.json'),('labels.json',PREV/'labels.json')]:shutil.copyfile(original,D/file)
sys.path.insert(0,str(D));import engine as e
e.write(D/'streams.json',e.keys())
plan={'schema':'payload-phase-known-reading-controls-v1','frozen_before':'control and target execution','revision':'f08b20b632d91209ddbaa747e8e2f23df0c78ba1','keys':'4 source payload streams mod29 tiled7times to1792; exact source PartB full55page allocation','grid':'4streams ×2signs ×offsets0..201 =1616 underlying controls. Known Warning184 if(stream ordinal+offset)even, LP2-56 85 otherwise. Atbash algebraic inversion plus16endpoint parity checks; no duplicated independent power count.','generator':'Unchanged encipher_keyskip, supp.83; firstseed3301..3332 withmaxskip<=3, allattempts/zero/noeligible retained. Controls test same key phase and sourcebeam, not complete target-grid selection or original page-assignment bounds.','gates':'Always evaluate diagnostic full beam300 separately from source50rune beam60 strict>−6.5→fullstrict>−5.5 gate. Source cumulative ranking and normalized acceptance unchanged.','wrong_key':'Next labelled variant insourceorder, samephase/sign; one diagnostic wrong key, no full-search null calibration.','decision':'If controls show recognition of known complete readings with adequate exact-recovery evidence and modest runtime, freeze target plan then run original30,112screen grid. Report limitations rather than delete failures.','inputs':[{'path':p.relative_to(D).as_posix(),'sha256':e.sha(p)} for p in sorted(D.rglob('*')) if p.is_file() and '__pycache__' not in p.parts]}
e.write(D/'control-plan.json',plan);print('Frozen',e.sha(D/'control-plan.json'))
