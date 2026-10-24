"""Finite offline technical replays and documentary coverage checks only."""
import gzip,hashlib,json,re,shutil,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent; SOURCE=HERE/'source'; ROOT=HERE.parents[2]
def load(p):return json.loads(p.read_bytes())
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
plan=load(HERE/'plan.json')
for r in plan['inputs']:assert hashlib.sha256((SOURCE/r['path']).read_bytes()).hexdigest()==r['sha256']
base='liber-primus/analysis/round18/L8-provenance/'
with tempfile.TemporaryDirectory() as td:
 tmp=Path(td);shutil.copytree(SOURCE,tmp,dirs_exist_ok=True)
 alias=plan['canonical_key_alias'];target=tmp/alias['target'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(tmp/alias['actual'],target)
 result=subprocess.run(['python',str(tmp/base/'compare_keys.py')],capture_output=True,text=True,timeout=180)
 assert result.returncode==0,result.stderr
 fresh=load(tmp/base/'KEY-COMPARISON.json')
 old=load(SOURCE/base/'KEY-COMPARISON.json')
 comparisons={k:fresh[k]==old[k] for k in ['comparison','verdict','verdict_inputs','base_rate_control']}
 # Save technical fields, excluding UID strings and local file paths from receipt.
 technical={'verdict':fresh['verdict'],'verdict_inputs':fresh['verdict_inputs'],'comparison':fresh['comparison'],'base_rate_control':fresh['base_rate_control'],'matches_archived':comparisons,'canonical_key_alias':alias,'limitation':'Shared defaults are nondiscriminating compatibility evidence; neither exact toolchain nor any identity is established. No revocation/signature verification was performed by --list-packets.'}
write(HERE/'key-technical-replay.json',technical)
# Exact source grep semantics: count case-insensitive matching LINES, not occurrences.
script=(SOURCE/base/'grep_archives.sh').read_text();terms=re.findall(r'^  "(.+)"$',script,re.M)[:16]
assert len(terms)==16
files=sorted((SOURCE/base/'evidence/archives').rglob('*.txt.gz'))
counts={t:0 for t in terms};by_file=[]
for f in files:
 data=gzip.decompress(f.read_bytes()).decode('latin1').splitlines()
 row={t:sum(bool(re.search(t,line,re.I|re.ASCII)) for line in data) for t in terms}
 for t,n in row.items():counts[t]+=n
 by_file.append({'file':str(f.relative_to(SOURCE)).replace('\\','/'),'matching_line_counts':row,'lines':len(data)})
oldgrep=(SOURCE/base/'evidence/archives/grep-results.txt').read_text()
archived_counts={t:int(re.search(r'^'+re.escape(t)+r'\s+(\d+)\s*$',oldgrep,re.M).group(1)) for t in terms}
assert counts==archived_counts,(counts,archived_counts)
coverage=load(SOURCE/'liber-primus/analysis/round19/C3/l8/predisclosure_archives.json')
write(HERE/'archive-technical-replay.json',{'scope':'16 fixed technical source patterns over held gzip blobs; excludes personal-handle terms and all new retrieval. Line counts, not dated-post authentication.','monthly_files':len(files),'months':[f.name.removesuffix('.txt.gz') for f in files],'matching_line_counts':counts,'all_saved_technical_counts_match':True,'by_file':by_file,'saved_coverage_keys':list(coverage),'limit':'Only 2011-August lies before Jan2012 in this held set; seven files are Jun-Dec2013. Zero matches in an uncovered month says nothing about that month. No new comprehensive pre-disclosure search or attested-post finding.'})
nav=['README.md','liber-primus/README.md','PICKUP-HERE.md','liber-primus/SOLVERS-DOSSIER.md'];navrows=[]
for p in nav:
 lines=(SOURCE/p).read_text(encoding='utf8').splitlines();matches=[{'line':i,'text':l} for i,l in enumerate(lines,1) if re.search(r'round[\s_-]*(?:9\b|IX\b)',l,re.I)]
 navrows.append({'path':p,'matches':matches})
ledger=(SOURCE/'research/LEDGER.md').read_text(encoding='utf8')
roadmap=(SOURCE/'AUTO_EVOLUTION.md').read_text(encoding='utf8')
write(HERE/'document-scope-check.json',{'declared_navigation_scope':navrows,'navigation_scope_note':'Four explicitly selected docs, not a claim that an unspecified set of all navigation docs has been recovered.','ledger_tally_still_five':bool(re.search(r'Executed statistical tests logged in THIS ledger: \*\*5\*\*',ledger)),'ledger_round_headings':re.findall(r'(?m)^#{1,2} Round .+$',ledger),'roadmap_latest_epoch':re.findall(r'(?m)^## Epoch .+$',roadmap)[0],'seek_proposals_present':{s:bool(re.search(r'(?m)^- '+s+r'\.',roadmap)) for s in ['S1','S2','S3']},'limit':'Navigation and tally maintenance checks are not cipher experiments. Five logged tests is not a defensible full-history multiplicity correction; no global effective-test count is inferred.'})
receipt={'schema':'residual-source-receipt-v1','plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),'pinned_input_count':len(plan['inputs']),'key_archived_field_comparisons':comparisons,'archive_files':len(files),'technical_patterns_replayed':len(terms),'archive_line_counts_match':True,'new_public_records':0,'network_calls':0}
write(HERE/'receipt.json',receipt);print(json.dumps(receipt,indent=2))
