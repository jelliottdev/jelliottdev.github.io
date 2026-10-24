"""Check batch membership and evidence bytes without treating audits as decryptions."""
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT.parent / 'source-cache/dukotah-cicada3301'


def main():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    expected = {entry['source_id'] for group in plan['groups'] for entry in group['entries']}
    assert len(expected) == 20
    seen, states = set(), Counter()
    verified = 0
    hashes = {}
    errors = []
    for receipt in sorted(HERE.glob('worker-*/receipt.json')):
        data = json.loads(receipt.read_text(encoding='utf-8'))
        assert data.get('source_revision', data.get('revision')) == plan['source_revision'], receipt
        for row in data['entries']:
            identifier = row['source_id']
            assert identifier in expected and identifier not in seen, identifier
            seen.add(identifier)
            states[row['state']] += 1
            assert row.get('covered_subclaim') and row.get('remaining') is not None, identifier
            for evidence in row.get('evidence', []):
                name, digest = evidence['path'], evidence['sha256']
                if name in hashes:
                    if hashes[name] != digest:
                        errors.append(identifier + ': inconsistent hash ' + name)
                    verified += 1
                    continue
                candidate = ROOT / name
                if Path(name).is_absolute():
                    raw = Path(name).read_bytes()
                elif candidate.is_file():
                    raw = candidate.read_bytes()
                else:
                    result = subprocess.run(['git', '-C', str(SOURCE), 'show',
                        plan['source_revision'] + ':' + evidence.get('source_path', name)], capture_output=True)
                    if result.returncode:
                        errors.append(identifier + ': missing ' + name)
                        continue
                    raw = result.stdout
                hashes[name] = hashlib.sha256(raw).hexdigest()
                if hashes[name] != digest:
                    errors.append(identifier + ': hash mismatch ' + name)
                verified += 1
    print(json.dumps({'entries_with_receipts': len(seen), 'planned': 20,
        'states': dict(states), 'evidence_objects_checked': verified,
        'awaiting_receipts': sorted(expected - seen), 'errors': errors}, indent=2))
    assert not errors, 'Evidence byte verification failed'


if __name__ == '__main__':
    main()
