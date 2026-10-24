"""Offline check of receipt hashes and its reproducible scoped audit products."""
import hashlib,json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent
R=H.parents[2]
S=R.parent/'source-cache/dukotah-cicada3301'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    rec=json.loads((H/'receipt.json').read_text())
    assert sha(H/'plan.json')==rec['plan_sha256']
    manifest=json.loads((H/'audit-source-manifest.json').read_text())
    for path,digest in manifest['files'].items():assert sha(S/path)==digest,path
    for name in ['audit.py','audit_saved.py']:
        subprocess.run([sys.executable,str(H/name)],check=True)
    for log in ['hitfn-after-english-recovery.txt','l5-after-english-recovery.txt']:
        text=(H/log).read_text()
        assert 'FileNotFoundError' in text and 'welsh_mabinogion.txt' in text
        assert 'ModuleNotFoundError' not in text
    assert len(rec['ledger_dispositions'])==5
    assert all(row['not_covered'] for row in rec['ledger_dispositions'])
    print('PASS: five bounded dispositions, source pins, exact English input, post-recovery Welsh blockers')
if __name__=='__main__':main()
