"""Audit saved original/guarded outputs and derive a comparison. No executable runs."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent/'outguess-default-key'
read = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def compare():
    plan, report, baseline = read(HERE/'plan.json'), read(HERE/'results/report.json'), read(BASE/'results/report.json')
    assert report['plan_sha256'] == sha(HERE/'plan.json')
    assert report['tool_sha256'] == plan['tool_sha256']
    for item in plan['inputs']:
        assert sha(ROOT/item['path']) == item['sha256']
    old = {r['image']: r for r in baseline['records']}
    assert len(old) == len(plan['images']) == len(report['records']) == 77
    assert set(old) == {i['id'] for i in plan['images']}
    rows = []
    for image, new in zip(plan['images'], report['records']):
        assert image['id'] == new['image']
        assert sha(ROOT/image['path']) == image['sha256'] == new['image_sha256']
        previous = old[image['id']]
        payloads = []
        for directory, record in ((HERE, new), (BASE, previous)):
            payload = (directory/'results'/record['output']).read_bytes() if record['output'] else None
            assert (hashlib.sha256(payload).hexdigest() if payload is not None else None) == record['sha256']
            assert (len(payload) if payload is not None else None) == record['bytes']
            payloads.append(payload)
        if image['id'] in plan['controls']:
            assert new['returncode'] == 0 and new['sha256'] == plan['controls'][image['id']]
        guards = [line for line in new['diagnostic'].splitlines() if line.startswith('Guard:')]
        rows.append({'image': image['id'], 'baseline_returncode': previous['returncode'],
                     'guarded_returncode': new['returncode'],
                     'same_diagnostic': new['diagnostic'] == previous['diagnostic'],
                     'same_payload_bytes': payloads[0] == payloads[1], 'guard_messages': guards})
    return {'schema': 'liberpedia-outguess-guard-comparison-v1',
            'plan_sha256': sha(HERE/'plan.json'), 'report_sha256': sha(HERE/'results/report.json'),
            'baseline_report_sha256': sha(BASE/'results/report.json'),
            'returncode_pairs': dict(Counter(str(r['baseline_returncode'])+' -> '+str(r['guarded_returncode']) for r in rows)),
            'same_diagnostics': sum(r['same_diagnostic'] for r in rows),
            'same_payload_bytes': sum(r['same_payload_bytes'] for r in rows), 'records': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = compare()
    path = HERE/'results/comparison.json'
    if args.check:
        assert read(path) == result
        print('PASS: saved comparison independently recomputed from 77 image/output pairs')
    else:
        with path.open('x', encoding='utf-8', newline='\n') as file:
            file.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'records'}))
