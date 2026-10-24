"""Reconcile the pinned, DRAFT handoff hierarchy with published records.

No categorization is inferred for new records. Run --check to verify saved bytes.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'research/research-map-source'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def build():
    provenance = load(SOURCE / 'provenance.json')
    for name, receipt in provenance['files'].items():
        assert sha((SOURCE / name).read_bytes()) == receipt['sha256'], name
    manifest = load(SOURCE / 'manifest.json')
    assert manifest['commit'] == provenance['source_commit']
    frozen_registry = next(f for f in manifest['files'] if f['path'] == 'data/experiments.json')
    assert frozen_registry['sha256'] == provenance['snapshot_experiments_sha256']
    assert frozen_registry['records'] == len(provenance['snapshot_record_sha256'])
    registry_path = ROOT / 'data/experiments.json'
    published = [r for r in load(registry_path)['records'] if r['status'] == 'published']
    current = {r['id']: r for r in published}
    assert len(current) == len(published), 'duplicate published record ID'
    snapshot = provenance['snapshot_record_sha256']
    views, assigned = {}, set()
    for view, filename in [('solving', 'solving-hierarchy.json'), ('analytics', 'analytics-hierarchy.json')]:
        source = load(SOURCE / filename)
        nodes = []
        for original in source['nodes']:
            node = {k: copy.deepcopy(original[k]) for k in
                    ('id', 'parent', 'label', 'color', 'kind', 'children', 'record_id', 'members', 'depth', 'x', 'left', 'right')}
            if node['record_id']:
                rid = node['record_id']
                assert rid in current and rid in snapshot, rid
                assert rid not in assigned, rid
                assigned.add(rid)
                node['label'] = current[rid]['title']
                node['draft_operation'] = original['operation_tag']
            nodes.append(node)
        ids = {n['id'] for n in nodes}
        assert len(ids) == len(nodes)
        assert all(n['parent'] in ids or n['parent'] is None for n in nodes)
        views[view] = {'root': nodes[0]['id'], 'title': source['report']['root_aim'],
                       'selection_rule': source['selection_rule'], 'nodes': nodes,
                       'record_count': len(nodes[0]['members']), 'classification_status': 'draft'}
    records = {}
    for rid, record in sorted(current.items()):
        fields = provenance['snapshot_fields_sha256'].get(rid, {})
        changed = sorted(k for k in record
                         if fields.get(k) != sha(canonical(record[k]))) if fields else []
        changed += sorted(set(fields) - set(record))
        records[rid] = {'id': rid, 'title': record['title'],
                        'question': record.get('reader_question') or record['question'],
                        'finding': record.get('reader_finding') or record['finding'],
                        'limitations': record.get('reader_limit') or record['limitations'],
                        'pages': record['scope']['pages'], 'scope': record['scope'],
                        'outcome': record['outcome'], 'href': '#/experiments/' + rid,
                        'current_sha256': sha(canonical(record)),
                        'snapshot_sha256': snapshot.get(rid), 'changed_fields': changed,
                        'classification': 'draft' if rid in assigned else
                            ('outside-selected-views' if rid in snapshot else 'awaiting-classification')}
    return {'schema': 'liberpedia-research-map-v1', 'classification_status': 'draft',
            'provenance': {'source_commit': provenance['source_commit'],
                           'snapshot_experiments_sha256': provenance['snapshot_experiments_sha256'],
                           'source_receipt_sha256': sha((SOURCE / 'provenance.json').read_bytes()),
                           'current_experiments_sha256': sha(registry_path.read_bytes()),
                           'source_files': provenance['files'], 'snapshot_records': len(snapshot),
                           'current_records': len(current), 'missing_snapshot_ids': sorted(set(snapshot) - set(current)),
                           'new_ids': sorted(set(current) - set(snapshot)),
                           'changed_ids': sorted(rid for rid in current if rid in snapshot and records[rid]['changed_fields'])},
            'views': views, 'records': records,
            'outside_selected_views': sorted((set(current) & set(snapshot)) - assigned),
            'awaiting_classification': sorted(set(current) - set(snapshot))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = build()
    content = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    target = ROOT / 'data/research-map.json'
    if args.check:
        assert target.read_bytes() == content, 'research-map.json is stale; rerun builder'
    else:
        target.write_bytes(content)
    print(json.dumps({k: v for k, v in data['provenance'].items() if k.endswith('_ids') or k.endswith('_records')}))


if __name__ == '__main__':
    main()
