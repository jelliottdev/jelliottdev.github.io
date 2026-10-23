"""Create the frozen, source-defined keyword-ramp plan without reading LP2 scores."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REV='bf89d3d13aad2b8f2c95ab195cf1b092f250775c'
SOURCE=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
def source_hash(path):
    raw=subprocess.check_output(['git','-C',str(SOURCE),'show',REV+':'+path])
    return hashlib.sha256(raw).hexdigest()
KEYS = {
  21: ('CABAL', [5,24,17,24,20]), 22: ('DIVINITY',[23,10,1,10,9,10,16,26]),
  23: ('ENCRYPTION',[18,9,5,4,26,13,16,10,3,9]), 24: ('OBSCURA',[3,17,15,5,1,4,24]),
  25: ('CABAL',[5,24,17,24,20]), 26: ('ENCRYPT',[18,9,5,4,26,13,16]),
  27: ('SHADOWS',[15,8,24,23,3,7,15]), 28: ('DEOR',[23,18,3,4]),
  29: ('TOTIENT',[16,3,16,10,18,9,16]), 30: ('MOURNFUL',[19,3,1,4,9,0,1,20])}
pages = []
for old, (name,key) in KEYS.items():
    site=f'lp2-{old-17:02d}'
    path=f'data/pages/{site}.json'
    pages.append({'source_page':old,'site_page':site,'site_path':path,
                  'site_sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),
                  'source_path':f'pages/page_{old:02d}/runes.txt',
                  'source_sha256':source_hash(f'pages/page_{old:02d}/runes.txt'),
                  'keyword':name,'seed':key})
known='data/evidence/known-readings.json'
plan={
 'schema':'wulfic-keyword-ramp-plan-v1',
 'timing':'retrospective source branch replay; branch, score and controls frozen before LP2 evaluation',
 'source_revision':REV,
 'source_script':'tools/legacy/advanced_cipher_solver.py',
 'source_script_sha256':'0872576665c6126da3839a0e9d67f994ac49859b641c2cfbf6b434d9bb9b20d9',
 'source_url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/'+REV+'/tools/legacy/advanced_cipher_solver.py',
 'pages':pages,
 'known_readings_path':known,
 'known_readings_sha256':hashlib.sha256((ROOT/known).read_bytes()).hexdigest(),
 'steps':[1,2,3,5,7,11,13,-1,-2],
 'rule':'P_i=(C_i-seed[i mod len(seed)]-i*step) mod 29; i resets at each page',
 'score':'source score_text: for each word in source COMMON_3PLUS, str.count(word)*len(word)^2 on concatenated GP labels; normalized 29xIoC is reported, not a selection gate',
 'observed_cases':90,
 'control':{'reading':'first-koan','source_page_slot':21,'planted_step':7,
            'require_exact_full_recovery':True,'require_true_case_top_source_score':True,
            'candidate_steps':'same nine-step source branch'},
 'null':{'trials':199,'seed':20261023,'method':'shuffle runes independently within each of the same ten pages once per trial, then retain the maximum source word score over all 90 cases; preserve each page histogram and keyword assignment'},
 'exclusions':'Source script other branches, other pages, other keywords, other steps, arbitrary language scoring and any claim that a source score verifies a plaintext.'}
HERE.mkdir(parents=True,exist_ok=True)
(HERE/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
print(HERE/'plan.json')
