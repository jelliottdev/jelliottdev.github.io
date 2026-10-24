"""Recover only the four exact small scorer inputs pinned by Dukotah's capsule."""
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[3].parent / 'source-cache' / 'dukotah-cicada3301'
M = json.loads((SOURCE / 'liber-primus/handoff/capsule/MANIFEST.json').read_text(encoding='utf-8'))
items = {x['id']: x for x in M['items'] if x.get('id') in ('corpus.kjv','corpus.moby','corpus.pride','corpus.war')}
assert len(items) == 4
dest = HERE / 'corpora'
dest.mkdir(exist_ok=True)
receipts = []
for label in ('kjv','moby','pride','war'):
    spec = items['corpus.' + label]
    target = dest / f'{label}.txt'
    if label == 'kjv':
        shutil.copyfile(SOURCE / spec['path'], target)
    elif not target.exists():
        request = urllib.request.Request(spec['mirrors'][0], headers={'User-Agent':'liberpedia-source-replay/1'})
        with urllib.request.urlopen(request, timeout=45) as response:
            target.write_bytes(response.read())
    data = target.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    match = (len(data), actual) == (spec['bytes'], spec['sha256'])
    receipts.append({'name':target.name,'bytes':len(data),'sha256':actual,'url':spec['mirrors'][0],
                     'expected_bytes':spec['bytes'],'expected_sha256':spec['sha256'],'exact_match':match})
    print('PASS' if match else 'FAIL', label, len(data), actual)
(HERE / 'corpora-receipt.json').write_text(json.dumps({'manifest':str(SOURCE / 'liber-primus/handoff/capsule/MANIFEST.json'), 'corpora':receipts},indent=2)+'\n', encoding='utf-8', newline='\n')
raise SystemExit(0 if all(x['exact_match'] for x in receipts) else 1)
