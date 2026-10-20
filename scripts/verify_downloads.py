"""Check every advertised download against working files or committed Git blobs."""
from pathlib import Path
import json,hashlib,subprocess,sys
root=Path(__file__).resolve().parents[1];use_git='--git' in sys.argv
catalog=json.loads((root/'data/catalog.json').read_text(encoding='utf-8'))
for f in catalog['files']:
 data=subprocess.run(['git','show','HEAD:'+f['path']],cwd=root,check=True,capture_output=True).stdout if use_git else (root/f['path']).read_bytes()
 assert len(data)==f['bytes'],f['path']+' size mismatch'
 assert hashlib.sha256(data).hexdigest()==f['sha256'],f['path']+' hash mismatch'
print('Verified',len(catalog['files']),'catalog entries against', 'committed Git bytes' if use_git else 'working files')
