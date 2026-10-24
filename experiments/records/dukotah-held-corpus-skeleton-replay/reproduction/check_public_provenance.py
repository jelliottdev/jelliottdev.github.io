"""Compare held raw bytes with the pinned public Git tree; no network calls."""
import replay as r
import subprocess, hashlib
tree=subprocess.check_output(['git','-C',str(r.SOURCE),'ls-tree','-r',r.REV],text=True)
index={line.split('\t',1)[1]:line.split('\t',1)[0].split()[2] for line in tree.splitlines()}
rows=[]
for item in r.read('inputs-frozen.json')['corpus']:
    b=(r.SOURCE/item['path']).read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    rows.append(dict(name=item['name'],path=item['path'],pinned_git_blob=index.get(item['path']),held_git_blob=blob,exact_pinned_public_blob=index.get(item['path'])==blob))
obj=dict(origin=subprocess.check_output(['git','-C',str(r.SOURCE),'config','--get','remote.origin.url'],text=True).strip(),revision=r.REV,exact_pinned_public_blobs=sum(x['exact_pinned_public_blob'] for x in rows),held_files=rows)
assert obj==r.read('corpus-public-provenance.json')
kjv=next(x for x in r.read('inputs-frozen.json')['corpus'] if x['name']=='data/kjv.txt')
old=r.REPO/'experiments/records/dukotah-offset-model-integrity'
receipt=__import__('json').loads((old/'corpora-receipt.json').read_text())
entry=next(x for x in receipt['corpora'] if x['name']=='kjv.txt')
assert entry['sha256']==kjv['sha256']==r.sha((old/'source-kjv.txt').read_bytes())
assert entry['bytes']==kjv['bytes'] and entry['exact_match']
license_path=r.SOURCE/'LICENSE';license_bytes=license_path.read_bytes()
assert license_bytes==subprocess.check_output(['git','-C',str(r.SOURCE),'show',r.REV+':LICENSE'])
assessment=dict(public_source=obj['origin'],revision=r.REV,exact_pinned_public_blobs=obj['exact_pinned_public_blobs'],local_kjv=dict(path=kjv['path'],bytes=kjv['bytes'],sha256=kjv['sha256'],recorded_public_url=entry['url'],local_alternative=(old/'source-kjv.txt').relative_to(r.REPO).as_posix(),prior_receipt=(old/'corpora-receipt.json').relative_to(r.REPO).as_posix(),prior_receipt_sha256=r.sha((old/'corpora-receipt.json').read_bytes()),availability='Recorded earlier exact download and current matching local bytes; URL not fetched/reverified in this replay.'),license=dict(path='LICENSE',sha256=r.sha(license_bytes),code_license='MIT; copyright 2026 Dukotah',limit='Public Git availability does not settle individual corpus text redistribution rights. No corpus redistribution proposed.'),reproduction='Obtain the pinned public repository plus exact KJV bytes at the recorded path; validate all raw and normalized hashes and exact loader membership before scanning. Fresh/current download bytes must match or stop; never substitute another edition.',minimal_bundle='Authored replay/check scripts, frozen plans and input hashes, saved outputs and audits, exact four L4 Python source files plus gematria.py, original MIT LICENSE and manuscript input. Exclude all94 corpus text files; accept only hash-validated external local inputs. No paid/API dependency.')
if (r.H/'publication-assessment.json').exists(): assert assessment==r.read('publication-assessment.json')
else:r.write('publication-assessment.json',assessment)
print('PASS:93 pinned public Git blobs; exact KJV matches earlier recorded download and local published artifact; no network.')
