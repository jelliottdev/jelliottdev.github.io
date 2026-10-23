"""Freeze exact Wulfic advanced-script running-key branch before target scoring."""
import hashlib,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[2]
REV='bf89d3d13aad2b8f2c95ab195cf1b092f250775c'
SOURCE=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
def blob(path):return subprocess.check_output(['git','-C',str(SOURCE),'show',REV+':'+path])
def sha(b):return hashlib.sha256(b).hexdigest()
PAGES=[21,22,23,24,25,26,27,28,29,30,31,32,33,34,43,44,49,54]
pages=[]
for n in PAGES:
    site=f'lp2-{n-17:02d}';sp=f'data/pages/{site}.json';sr=f'pages/page_{n:02d}/runes.txt';sb=(ROOT/sp).read_bytes()
    pages.append({'source_page':n,'site_page':site,'site_path':sp,'site_sha256':sha(sb),
                  'source_path':sr,'source_sha256':sha(blob(sr)),'runes':json.loads(sb)['rune_count']})
corpora=[]
for key,name in [('LiberAL','liber_al_vel_legis'),('SelfReliance','self_reliance'),('Deor','deor_poem')]:
    path=f'data/corpora/{name}.txt';b=blob(path)
    corpora.append({'name':key,'source_path':path,'source_sha256':sha(b),'bytes':len(b),
                    'encoding':'source text_to_gp_indices'})
corpora.insert(1,{'name':'SolvedLP','source_path':'embedded load_solved_plaintext in source script',
                  'source_sha256':None,'encoding':'literal source known_texts → source text_to_gp_indices'})
known='data/evidence/known-readings.json'
layout='data/pages/lp1-06.json'
plan={
 'schema':'wulfic-advanced-running-keys-plan-v1',
 'timing':'Retrospective source branch; grid, source score and power gates frozen before current target scores.',
 'source_revision':REV,'source_script':'tools/legacy/advanced_cipher_solver.py',
 'source_script_sha256':sha(blob('tools/legacy/advanced_cipher_solver.py')),
 'source_url':'https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/'+REV+'/tools/legacy/advanced_cipher_solver.py',
 'pages':pages,'corpora':corpora,'known_readings_path':known,'known_readings_sha256':sha((ROOT/known).read_bytes()),
 'control_layout_path':layout,'control_layout_sha256':sha((ROOT/layout).read_bytes()),
 'source_calls':'method 5 of test_page on 18 priority pages; four running_keys in main order LiberAL, SolvedLP, SelfReliance, Deor',
 'coarse':'for each page/key, offset range(0, key_length−page_length, 100); test sub, add, beaufort in that order; choose strictly largest normalized 29×IoC, ties keep first',
 'refine':'for offset in range(max(0,best_offset−100),min(key_length−page_length,best_offset+100)) in selected direction only; strict greater IoC updates; upper endpoint excluded',
 'score':'source score_text(concatenated GP labels) + score_with_structure(original rune content, final decoded indices, None), plus source sort key score+50×normalized IoC',
 'selection':'retain one final offset/direction/output per page/key; compare all 72 returned method-5 candidates, not all positions or other source methods',
 'control':{'reading':'first-koan','true_page_slot':21,'on_grid_offset':300,'off_grid_offset':137,
            'one_page':'for each of all four source corpora, encrypt the unchanged complete known reading with key segment at each of the two declared offsets and score with its original LP1-06 rune-word layout; source coarse/refine selector must recover all 209 runes for every on-grid plant; off-grid misses are retained without retuning',
            'whole_grid':'LiberAL on-grid plant in source page21 slot and seeded uniform GP29 arrays in 17 other slots at their declared lengths; test all 72 page/key winners and require full exact recovery and first source rank',
            'seed':1982031},
 'null':{'trials':49,'seed':20261026,'method':'shuffle each actual source page independently once per trial; rerun all 72 source page/key selectors; retain the best source score+50×IoC, with a shared shuffled corpus across all keys'},
 'source_overlap':'Deor/Self-Reliance are earlier tested under p21_30_solver on ten pages; Liber AL under a different p25 selector on one page; SolvedLP here is the authored source literal, not canonical audited rune readings.',
 'exclusions':'Other key texts/editions, unsampled offsets, other source methods, alternate Greek/Roman encodings, interrupted clocks and whole-book joined streams.'}
H.mkdir(parents=True,exist_ok=True)
(H/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
print(H/'plan.json')
