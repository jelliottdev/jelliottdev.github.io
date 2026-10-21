"""Check saved pilot evidence and its bounded comparison; does not execute OutGuess."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
plan = json.loads((HERE/'plan.json').read_bytes())
report = json.loads((HERE/'results/report.json').read_bytes())
baseline = json.loads((HERE.parent/'outguess-default-key/results/report.json').read_bytes())
assert report['plan_sha256'] == sha(HERE/'plan.json')
assert report['tool_sha256'] == plan['tool_sha256']
rows = report['records']
assert [r['image'] for r in rows] == [i['id'] for i in plan['images']]
assert len(rows) == 13 and len(plan['controls']) == 10
before = {r['image']: r for r in baseline['records']}
for image, row in zip(plan['images'], rows):
    assert sha(ROOT/image['path']) == image['sha256'] == row['image_sha256']
    output = HERE/'results'/row['output']
    assert sha(output) == row['sha256'] and output.stat().st_size == row['bytes']
    if row['image'] in plan['controls']:
        assert row['returncode'] == 0 and row['sha256'] == plan['controls'][row['image']]
    assert row['sha256'] == before[row['image']]['sha256']
after = {r['image']: r for r in rows}
for page in ('lp1-06', 'lp1-05'):
    assert after[page]['returncode'] == before[page]['returncode']
    assert after[page]['diagnostic'] == before[page]['diagnostic']
assert before['lp1-14']['returncode'] == 3221225620
assert after['lp1-14']['returncode'] == 1
assert 'Guard: iterator skipmod zero at off=645437 bits=645682' in after['lp1-14']['diagnostic']
print('PASS: 13 image/output bindings, ten controls, two unchanged cases, one explicit guard rejection')
