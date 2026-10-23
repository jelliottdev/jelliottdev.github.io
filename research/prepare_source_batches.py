"""Prepare pinned source evidence once and schedule pending entries in shared-source batches.

This is internal triage, not experiment execution or a coverage verdict.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'f08b20b632d91209ddbaa747e8e2f23df0c78ba1'


def tree(repo, revision):
    result = subprocess.check_output(['git', '-C', str(repo), 'ls-tree', '-r', '--long', revision])
    rows = {}
    for line in result.decode('utf-8').splitlines():
        info, path = line.split('\t', 1)
        mode, kind, oid, size = info.split()
        rows[path] = {'git_object': oid, 'bytes': int(size) if size != '-' else None,
                      'kind': kind, 'mode': mode}
    return rows


def resolve(path, objects):
    path = unquote(path.split('#', 1)[0]).strip().rstrip('/')
    possibilities = [path]
    if not path.startswith('liber-primus/'):
        possibilities.append('liber-primus/' + path)
    found = [{'path': p, **objects[p]} for p in possibilities if p in objects]
    if found:
        return {'requested': path, 'status': 'ambiguous' if len(found) > 1 else
                'exact' if found[0]['path'] == path else 'prefix-adjusted', 'candidates': found}
    members = sorted(p for p in objects if any(p.startswith(q + '/') for q in possibilities))
    if not members:
        suffixes = sorted(p for p in objects if p.endswith('/' + path))
        if suffixes:
            return {'requested': path,
                    'status': 'suffix-adjusted' if len(suffixes) == 1 else 'ambiguous',
                    'candidates': [{'path': p, **objects[p]} for p in suffixes]}
    return {'requested': path, 'status': 'directory' if members else 'not-in-pinned-tree',
            'members': members, 'candidates': []}


def prepare(inventory, objects, revision=REVISION, batch_count=3):
    entries = [r for r in inventory['entries'] if 'reviewed_subclaims' not in r]
    by_id = {r['source_id']: r for r in entries}
    assert len(by_id) == len(entries)
    parent = {key: key for key in by_id}
    def find(key):
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key
    def union(a, b):
        parent[find(b)] = find(a)
    owners = defaultdict(list)
    prepared = []
    for entry in entries:
        command = entry.get('source_reproduction_command') or ''
        paths = set()
        for url in entry.get('source_evidence_urls', []):
            marker = '/blob/' + revision + '/'
            if marker in url:
                paths.add(url.split(marker, 1)[1])
        paths.update(re.findall(r'(?:liber-primus/)?analysis/[^\s\"\';|&]+', command))
        evidence = [resolve(p, objects) for p in sorted(paths)]
        if command.strip():
            owners['command:' + ' '.join(command.split())].append(entry['source_id'])
        for item in evidence:
            if len(item['candidates']) == 1 and item['candidates'][0]['path'].endswith('.py'):
                owners['script:' + item['candidates'][0]['path']].append(entry['source_id'])
        prepared.append({'source_id': entry['source_id'], 'hypothesis': entry['source_hypothesis'],
                         'source_claimed_status': entry.get('source_status'),
                         'command': command, 'evidence': evidence,
                         'candidate_records': entry.get('candidate_records', [])})
    for ids in owners.values():
        for ident in ids[1:]:
            union(ids[0], ident)
    groups = defaultdict(list)
    for entry in prepared:
        groups[find(entry['source_id'])].append(entry)
    ordered = sorted(groups.values(), key=lambda g: (-len(g), min(e['source_id'] for e in g)))
    batches = [{'batch': n + 1, 'entry_count': 0, 'groups': []} for n in range(batch_count)]
    for group in ordered:
        batch = min(batches, key=lambda b: (b['entry_count'], b['batch']))
        batch['groups'].append({'source_ids': sorted(e['source_id'] for e in group), 'entries': group})
        batch['entry_count'] += len(group)
    assigned = [e['source_id'] for b in batches for g in b['groups'] for e in g['entries']]
    assert len(assigned) == len(set(assigned)) == len(entries) and set(assigned) == set(by_id)
    return {'schema': 'internal-pinned-source-batches-v1', 'revision': revision,
            'usage': 'Scheduling only. Shared commands/scripts do not prove identical methods or coverage. '
                     'Evidence presence is not complete input availability. Inspect exact controls and branches.',
            'pending_entry_count': len(entries), 'shared_source_group_count': len(groups), 'batches': batches}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT.parent / 'source-cache/dukotah-cicada3301')
    parser.add_argument('--output', type=Path, default=ROOT / 'research/source-batches-2026-10-23.json')
    args = parser.parse_args()
    source = ROOT / 'research/public-attempt-inventory.json'
    raw = source.read_bytes()
    inventory = json.loads(raw)
    assert inventory['source']['revision'] == REVISION
    pack = prepare(inventory, tree(args.repo, REVISION))
    pack['inventory_sha256'] = hashlib.sha256(raw).hexdigest()
    args.output.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f"Prepared {pack['pending_entry_count']} entries in {pack['shared_source_group_count']} groups; batches "
          + ', '.join(str(b['entry_count']) for b in pack['batches']))
