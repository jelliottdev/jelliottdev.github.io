"""Freeze the source's complete fixed-keyword LFSR branch before LP2 scoring."""
import hashlib,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[2]
REV='bf89d3d13aad2b8f2c95ab195cf1b092f250775c'
SOURCE=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
def sha(data):return hashlib.sha256(data).hexdigest()
def source_hash(path):return sha(subprocess.check_output(['git','-C',str(SOURCE),'show',REV+':'+path]))
KEYS={21:('CABAL',[5,24,17,24,20]),22:('DIVINITY',[23,10,1,10,9,10,16,26]),
      23:('ENCRYPTION',[18,9,5,4,26,13,16,10,3,9]),24:('OBSCURA',[3,17,15,5,1,4,24]),
      25:('CABAL',[5,24,17,24,20]),26:('ENCRYPT',[18,9,5,4,26,13,16]),
      27:('SHADOWS',[15,8,24,23,3,7,15]),28:('DEOR',[23,18,3,4]),
      29:('TOTIENT',[16,3,16,10,18,9,16]),30:('MOURNFUL',[19,3,1,4,9,0,1,20])}
pages=[]
for source_page,(name,key) in KEYS.items():
    site=f'lp2-{source_page-17:02d}';path=f'data/pages/{site}.json';data=(ROOT/path).read_bytes()
    pages.append({'source_page':source_page,'site_page':site,'site_path':path,'site_sha256':sha(data),
                  'runes':json.loads(data)['rune_count'],'source_path':f'pages/page_{source_page:02d}/runes.txt',
                  'source_sha256':source_hash(f'pages/page_{source_page:02d}/runes.txt'),
                  'keyword':name,'keyword_indices':key})
known='data/evidence/known-readings.json'
plan={'schema':'wulfic-keyword-lfsr-plan-v1',
      'timing':'retrospective source branch audit; frozen grid and gates before LP2 evaluation',
      'source_revision':REV,'source_script':'tools/legacy/advanced_cipher_solver.py',
      'source_script_sha256':source_hash('tools/legacy/advanced_cipher_solver.py'),
      'source_url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/'+REV+'/tools/legacy/advanced_cipher_solver.py',
      'pages':pages,'known_readings_path':known,'known_readings_sha256':sha((ROOT/known).read_bytes()),
      'degrees':[4,5,6,7,8],
      'tap_lists':'For degree d: [1,d−1], [1,2], [2,d−1], [1,...,d−1] in this order; no tap 0',
      'initial_state':'page keyword indices repeated enough and truncated to degree d',
      'feedback':'Emit state[0]; calculate sum(state[t] for t in taps) mod29 on the old state; then delete state[0] and append feedback',
      'modes':['sub','beaufort'],
      'decode':'sub: P=(C−K)%29; beaufort: P=(K−C)%29; page-local key starts at state[0]',
      'gate':'source method6 reports a candidate only if full decoded-page normalized 29×IoC > 1.2, then uses source score_text on concatenated GP labels',
      'selection':'For a reported candidate use source sort score_text + 50×normalized_IoC. Retain all 400 case gate/score/digests and the single maximum per whole grid.',
      'control':{'reading':'first-koan','source_page_slot':21,'degree':5,'tap_index':0,'mode':'sub',
                 'other_slots':'independent seeded uniform GP29 rune arrays matching the nine unmodified source-page lengths',
                 'seed':1982026,'requirements':['exact full 209-rune recovery','normalized_IoC>1.2','true candidate ranks first across complete ten-slot/400-case control grid']},
      'null':{'trials':199,'seed':20261024,
              'method':'shuffle each original LP2 page independently once per trial; test the same 400-case source grid; retain number above gate and top reported rank score; share each shuffled corpus across all methods'},
      'observed_cases':400,
      'exclusions':'Other LFSR states/taps, arbitrary key lengths, other pages, character skips, resets within pages and source branches 1–5/7.'}
H.mkdir(parents=True,exist_ok=True)
(H/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
print(H/'plan.json')
