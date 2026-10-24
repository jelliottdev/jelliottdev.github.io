"""Finite source-bound audit; no cipher search or source-prior promotion."""
import collections,hashlib,json,re,subprocess,sys,types,math,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REV='f08b20b632d91209ddbaa747e8e2f23df0c78ba1'
M=json.loads((HERE/'source-manifest.json').read_text())['sources']
# Reuse the shared pinned checkout instead of committing another 13.5 MB signed blob.
for source_path, meta in M.items():
 destination=ROOT/meta['path']
 if not destination.exists():
  raw=subprocess.check_output(['git','-C',str(ROOT.parent/'source-cache/dukotah-cicada3301'),'show',REV+':'+source_path],timeout=60)
  assert hashlib.sha256(raw).hexdigest()==meta['sha256'],source_path
  destination.parent.mkdir(parents=True,exist_ok=True)
  destination.write_bytes(raw)
def read(suffix):
 key=next(k for k in M if k.endswith(suffix));p=ROOT/M[key]['path'];raw=p.read_bytes()
 assert hashlib.sha256(raw).hexdigest()==M[key]['sha256']
 return raw
def document(suffix):return json.loads(read(suffix))
def module(suffix):
 mod=types.ModuleType('pinned_source');mod.__file__=str(HERE/'sources'/('source-'+Path(suffix).name))
 exec(compile(read(suffix),suffix,'exec'),mod.__dict__);return mod
out={'revision':REV,'scope':'Finite source corrections and provenance subsets, not LP2 cipher exclusions.'}
# Independently verify all 56 supplied files with an isolated public-only keyring.
key='corpus/A-primary-artifacts/ibotpeaches/keys/67F363C61BA8FB6FDBA9C47D0670B0E57A35090F.asc'
raw=subprocess.check_output(['git','-C',str(ROOT.parent/'source-cache/dukotah-cicada3301'),'show',REV+':'+key],timeout=60)
keyfile=HERE/'key.asc';keyfile.write_bytes(raw)
assert hashlib.sha256(raw.replace(b'\n',b'\r\n')).hexdigest()=='75655aef4fd7db91a4bb75c1c6ac6e00d08fe836a28bf5efd88a7c3363637d1c'
out['key_line_endings']={'git_lf_sha256':hashlib.sha256(raw).hexdigest(),'source_table_crlf_sha256':hashlib.sha256(raw.replace(b'\n',b'\r\n')).hexdigest()}
home=HERE/'gnupg';home.mkdir(exist_ok=True)
gpg=shutil.which('gpg');base=[gpg,'--no-options','--batch','--homedir',str(home),'--no-auto-key-retrieve','--no-autostart']
imp=subprocess.run(base+['--import',str(keyfile)],capture_output=True,timeout=20)
assert imp.returncode==0,imp.stderr
rows=[];versions=collections.Counter();timestamps=[];bodyhashes=set();sighashes=set()
for path,meta in sorted(M.items()):
 if '/ibotpeaches/messages/' not in path:continue
 raw=(ROOT/meta['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==meta['sha256']
 text=raw.decode('utf-8',errors='replace')
 r=subprocess.run(base+['--status-fd','1','--allow-weak-digest-algos','--verify',str(ROOT/meta['path'])],capture_output=True,timeout=30)
 status=r.stdout.decode('utf-8',errors='replace');valid=re.findall(r'\[GNUPG:\] VALIDSIG (\w+) (\S+) (\d+)',status)
 sig=re.search(r'-----BEGIN PGP SIGNATURE-----(.*?)-----END PGP SIGNATURE-----',text,re.S)
 ver=re.search(r'^Version: (.+)$',sig[1],re.M).group(1).strip() if sig else None
 versions[ver]+=1
 if sig:sighashes.add(hashlib.sha256(''.join(sig[1].split('\n\n',1)[-1].split()).encode()).hexdigest())
 assert valid and all(v[0]=='6D854CD7933322A601C3286D181F01E57A35090F' for v in valid),path+' '+status+r.stderr.decode(errors='replace')
 timestamps += [v[2] for v in valid]
 body=text.split('\n\n',1)[-1].split('-----BEGIN PGP SIGNATURE-----')[0]
 bodyhashes.add(hashlib.sha256(body.encode()).hexdigest())
 rows.append({'path':path,'sha256':meta['sha256'],'returncode':r.returncode,'version':ver,'validsig':valid,'status':status})
out['message_verification']={'files':len(rows),'validsig_files':sum(bool(r['validsig']) for r in rows),'distinct_signature_timestamps':len(set(timestamps)),'signature_payloads':len(sighashes),'armor_versions':dict(versions),'earliest_date':min(v[1] for row in rows for v in row['validsig']),'latest_date':max(v[1] for row in rows for v in row['validsig']),'rows':rows}
print('Signature measurements',len(rows),len(set(timestamps)),dict(versions),flush=True)
clear=[r for r in rows if r['version'] is not None]
clear_times={v[2] for r in clear for v in r['validsig']}
assert len(rows)==57 and len(set(timestamps))==55 and len(clear)==56 and len(clear_times)==54
out['message_verification']['clear_signed_files']=56
out['message_verification']['clear_signed_distinct_timestamps']=54
out['message_verification']['source_56_54_scope']='Clear-signed files only; excludes tcp-server.asc with an embedded PGP MESSAGE signature.'
assert {k:v for k,v in versions.items() if k is not None}=={'GnuPG v1.4.11 (GNU/Linux)':53,'GnuPG v1':2,'CicadaPG v.3301':1}
table=document('round19/C3/PGP-VERIFICATION-TABLE.json')
source_rows={r['path']:r for r in table['rows'] if '/ibotpeaches/messages/' in r['path']}
assert set(source_rows)=={r['path'] for r in rows}
line_ending_counts=collections.Counter();verdict_differences=[]
for row in rows:
 b=(ROOT/M[row['path']]['path']).read_bytes();expected=source_rows[row['path']]['sha256']
 mode='exact' if hashlib.sha256(b).hexdigest()==expected else 'CRLF-equivalent' if hashlib.sha256(b.replace(b'\n',b'\r\n')).hexdigest()==expected else 'mismatch'
 line_ending_counts[mode]+=1
 assert mode!='mismatch'
 if source_rows[row['path']]['verdict']!='PASS':verdict_differences.append({'path':row['path'],'source_verdict':source_rows[row['path']]['verdict'],'actual_validsig':row['validsig']})
out['message_verification']['source_table_comparison']=dict(line_ending_counts)
out['message_verification']['source_verdict_differences']=verdict_differences
(HERE/'signature-results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
# Signed textual evidence of Crypt::RSA is checked separately from its keystream relevance.
out['crypt_rsa_files']=[r['path'] for r in rows if 'Crypt::RSA' in (ROOT/M[r['path']]['path']).read_text(encoding='utf-8',errors='replace')]
# Execute exact pinned JPEG parser on source-hash-verified available LP2 inputs.
fp=module('round18/L1-toolchain/jpeg_fingerprint.py')
recovery=json.loads((ROOT/'research/source-intake/dukotah-image-input-recovery-2026-10-23.json').read_text())
classes=collections.Counter();image_rows=[]
for row in recovery['lp2_source_images']:
 path=Path(row['hosted_local_path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==row['source_expected_sha256']
 parsed=fp.fingerprint(str(path));v=parsed['fingerprint_vector'];classes[str(v['ncomp'])]+=1
 image_rows.append({'page':row['source_page'],'sha256':row['source_expected_sha256'],'vector':v})
out['jpeg_parser_replay']={'source_verified_images':len(image_rows),'component_counts':dict(classes),'rows':image_rows,'missing_source_pages':['p56.jpg','p57.jpg'],'does_not_cover':'Ghostscript historical build/render chain, font face match or PDF text-layer hunt.'}
assert len(image_rows)==56
# Exact source arithmetic, not a hardware rerun or survival Monte Carlo.
d=document('round19/R1/out_d.json');rate=d['D_a_throughput']['L120']['union2/ms3']['decodes_per_sec'];arith=[]
for row in d['D_a_spaces']:
 expected=row['seeds']*8;seconds=expected/rate/6
 assert row['decodes']==expected and math.isclose(row['sec_union2_6core'],seconds,rel_tol=1e-12)
 arith.append({'space':row['space'],'decodes':expected,'source_rate_decodes_per_second_per_core':rate,'six_core_seconds':seconds})
assert math.isclose(d['D_iii']['fraction'],d['D_iii']['stored']/d['D_iii']['total_scored'],rel_tol=1e-12)
out['r1_budget_arithmetic']={'spaces':arith,'retained_fraction':d['D_iii'],'source_prefilter_survival':d['D_b_prefilter'],'limit':'Arithmetic from source-saved rates only. Throughput timing, survival draws and stored-candidate recount are not independently rerun.'}
# Prior multiplier warnings are explicit source assertions, not measured likelihoods.
c=module('round19/R1/c_prior.py');out['r1_shift_audit']=c.shift_audit()
g=module('round19/G4/allrunes_probe.py');saved=document('round19/G4/allrunes_probe.json')
assert len(g.NAME)==len(set(g.NAME.values()))==saved['n_runes_compared']==26
assert list(g.NAME)==saved['runes_compared']
# A synthetic algebra control licenses only fit arithmetic, not font identification.
pred={k:i+1 for i,k in enumerate(g.NAME)};obs={k:0.7*v for k,v in pred.items()};scale,rms=g.fit(pred,obs,list(g.NAME));assert abs(scale-0.7)<1e-12 and rms<1e-12
out['allrunes']={'mapped_names':g.NAME,'synthetic_fit_control':{'planted_scale':0.7,'recovered_scale':scale,'rms':rms},'source_faces':saved['n_faces'],'source_skipped':saved['n_skipped'],'source_best':saved['top10'][0],'source_control':saved['permutation_control'],'limit':'Font bank and observed glyph bitmaps are absent from pinned Git. No actual face-width ranking or 200-permutation screen rerun.'}
(HERE/'audit-results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ['message_verification','jpeg_parser_replay','r1_shift_audit']},indent=2))
print('VERIFIED',len(rows),'signed files;',len(set(timestamps)),'timestamps;',len(image_rows),'JPEG parser inputs; source budget arithmetic and26-name mapping control passed.')
