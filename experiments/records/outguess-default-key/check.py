"""Audit saved retrieval records, hashes and controls without running OutGuess."""
import hashlib
import json
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()
plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
report=json.loads((HERE/'results/report.json').read_text(encoding='utf-8'))
assert report['plan_sha256']==sha((HERE/'plan.json').read_bytes())
assert len(report['records'])==len(plan['images'])==77
assert [r['image'] for r in report['records']]==[r['id'] for r in plan['images']]
for row,image in zip(report['records'],plan['images']):
    assert row['image_sha256']==image['sha256']==sha((ROOT/image['path']).read_bytes())
    if row['output']:
        data=(HERE/'results'/row['output']).read_bytes()
        assert len(data)==row['bytes'] and sha(data)==row['sha256']
    else:
        assert row['bytes'] is None and row['sha256'] is None
    expected=plan['controls'].get(row['image'])
    if expected:
        assert row['returncode']==0 and row['sha256']==expected and row['status']=='control-match'
    elif row['status']=='candidate-output':
        assert row['returncode']==0 and row['bytes']>0
print('All 77 original hashes, output hashes and known-control comparisons pass.')
print(dict(Counter(r['returncode'] for r in report['records'])))
print('This audit does not authenticate candidate bytes or explain tool failures.')
