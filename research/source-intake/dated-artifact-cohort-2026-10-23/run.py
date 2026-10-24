"""Replay only preserved source extraction, with no network or decoder imports."""
import base64, hashlib, json, re, runpy, subprocess, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=HERE/'source'
def load(p): return json.loads(p.read_bytes())
def write(p,v): p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
plan=load(HERE/'plan.json')
for row in plan['inputs']:
 assert hashlib.sha256((SOURCE/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
# Read-only source inputs copied to isolated writable directory: source writes never touch pin.
with tempfile.TemporaryDirectory() as td:
 import shutil
 sandbox=Path(td)
 shutil.copytree(SOURCE,sandbox,dirs_exist_ok=True)
 c8=sandbox/'liber-primus/analysis/round24/C8-date-indexed-pad'
 l8=sandbox/'liber-primus/analysis/round18/L8-provenance'
 c8out=subprocess.check_output(['python',str(c8/'step0_timestamps.py')],text=True)
 g09out=subprocess.check_output(['python',str(l8/'build_seed_candidates.py')],text=True)
 c8result=load(c8/'cache/timestamps.json'); prior=load(l8/'TIMESTAMP-SEED-CANDIDATES.json')
write(HERE/'c8-step0-replay.json',c8result)
write(HERE/'g09-prior-replay.json',prior)
# An independent parser supports complete packet lengths, without source helper code.
def packet_creation(payload):
 raw=base64.b64decode(''.join(l.strip() for l in payload.splitlines() if l.strip() and not l.startswith(('Version:','Comment:','='))))
 head=raw[0]
 if head&64:
  n=raw[1]
  if n<192: off=2; length=n
  elif n<224: off=3; length=(n-192)*256+raw[2]+192
  elif n==255: off=6; length=int.from_bytes(raw[2:6],'big')
  else: raise ValueError('partial length outside frozen scope')
 else:
  widths={0:1,1:2,2:4}; width=widths[head&3]; off=1+width; length=int.from_bytes(raw[1:off],'big')
 d=raw[off:off+length]; assert d[0]==4
 data=d[6:6+int.from_bytes(d[4:6],'big')]; stamps=[]
 while data:
  n=data[0]; assert n<192
  sub=data[1:1+n]; data=data[1+n:]
  if sub[0]&127==2: stamps.append(int.from_bytes(sub[1:],'big'))
 assert len(stamps)==1
 return stamps[0]
text=(SOURCE/'liber-primus/data/scream314_lp.md').read_text(encoding='utf8')
plain='\n'.join(l[4:] if l.startswith('    ') else l for l in text.splitlines())
headers=list(re.finditer(r'(?m)^(#{1,2}) (.+)$',plain))
rows=[]
for m in re.finditer(r'-----BEGIN PGP SIGNATURE-----\n(.*?)-----END PGP SIGNATURE-----',plain,re.S):
 prev=[h for h in headers if h.start()<m.start()]
 rows.append({'part':next(h.group(2) for h in reversed(prev) if h.group(1)=='#'),'section':prev[-1].group(2),'sig_creation_unix':packet_creation(m.group(1))})
lp2=plain.split('# LP2\n',1)[1].split('# Magic Squares',1)[0]
lp2sections=re.findall(r'(?m)^## (.+)$',lp2)
assert [(r['section'],r['sig_creation_unix']) for r in rows]==[(r['section'],r['sig_creation_unix']) for r in c8result['signed_blocks']]
assert all(r['part']=='LP1' for r in rows)
archived=load(SOURCE/'liber-primus/analysis/round18/L8-provenance/TIMESTAMP-SEED-CANDIDATES.json')
assert {k:v for k,v in prior.items() if k!='generated_utc'}=={k:v for k,v in archived.items() if k!='generated_utc'}
# Independently verify finite arithmetic derivation set (nine outputs per included time).
from datetime import datetime,timezone
messages=load(SOURCE/'liber-primus/analysis/round18/L8-provenance/MESSAGES.json')
stamps=[m['signature_timestamp_unix'] for m in messages['messages'] if m['verdict']=='PASS' and m['signature_timestamp_unix']]+[1325734783]*3+[1325635200,1326067200]
seeds=set()
for t in stamps:
 d=datetime.fromtimestamp(t,timezone.utc)
 seeds.update([t,t-1,t+1,t-t%60,t-t%3600,t-t%86400,int(d.strftime('%Y%m%d')),int(d.strftime('%Y%m%d%H%M%S')),t*1000])
assert seeds=={c['seed'] for c in prior['candidates']}
# Current G02 receipt comparison is explicitly against current pinned bytes, not old table claims.
g02=load(ROOT/'experiments/records/dukotah-g02-signature-corpus/independent-verification.json')
receipt={'schema':'dated-artifact-cohort-receipt-v1','source_revision':plan['source_revision'],'plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),'verified_input_count':len(plan['inputs']),'C8':{'signed_blocks':len(rows),'distinct_signature_seconds':len(set(r['sig_creation_unix'] for r in rows)),'blocks_by_part':{'LP1':sum(r['part']=='LP1' for r in rows),'LP2':sum(r['part']=='LP2' for r in rows)},'independent_packet_and_section_rows':rows,'lp2_markdown_sections':len(lp2sections),'lp2_section_titles':lp2sections,'lp2_signature_markers':lp2.count('-----BEGIN PGP SIGNATURE-----'),'runic_transcription_segments':c8result['decrypt_target']['n_pages'],'scope':'Absence of the proposed join in these two preserved textual inputs only; not an LP2 cryptanalytic negative.','archived_630_decoder_rows_replayed':False,'beacon_cache_xml_files_in_pin':0},'G09':{'source_timestamp_count':prior['source_timestamp_count'],'source_timestamps_verified_label':prior['source_timestamps_verified'],'candidate_count':prior['candidate_count'],'tier_counts':prior['tier_counts'],'all_archived_fields_match_except_generation_time':True,'independent_seed_set_match':True,'current_G02_distinct_verified_timestamps':g02['distinct_verified_timestamps'],'caution':'Source verified labels are archival and clocks remain signer-settable; current G02 has a different snapshot. No RNG seed was tested.'},'stdout':{'C8':c8out,'G09':g09out}}
write(HERE/'receipt.json',receipt)
print(json.dumps({k:v for k,v in receipt.items() if k!='stdout'},indent=2))
