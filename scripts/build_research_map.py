"""Reconcile the pinned, DRAFT handoff hierarchy with published records.

No categorization is inferred for new records. Run --check to verify saved bytes.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from experiment_content import SCHEMA, draft_record_ids

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'research/research-map-source'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def retired_ids(root):
    """Only canonical v2 drafts explicitly authorize withdrawal from the map."""
    return set(draft_record_ids(root))


def place_classified(views, current, retired=()):
    """Apply explicit record parents to a copy; preserve unchanged source trees."""
    views = copy.deepcopy(views)
    locations, leaves = {}, {}
    for name, view in views.items():
        assert name in ('solving', 'analytics'), 'Unsupported classification view'
        for node in view['nodes']:
            assert node['id'] not in locations, 'Ambiguous map parent: ' + node['id']
            locations[node['id']] = (name, node)
            if node['record_id']:
                assert node['record_id'] not in leaves, 'Duplicate map record'
                leaves[node['record_id']] = node
    changed_views = set()
    for rid in sorted(set(retired)):
        assert rid not in current, 'Draft record remains in published registry: ' + rid
        leaf = leaves.pop(rid, None)
        if leaf is None:
            continue
        name, _ = locations.pop(leaf['id'])
        locations[leaf['parent']][1]['children'].remove(leaf['id'])
        views[name]['nodes'].remove(leaf)
        changed_views.add(name)
    for rid, record in sorted(current.items()):
        classification = record.get('classification')
        if classification is None:
            continue
        parent_id = classification.get('map_parent') if isinstance(classification, dict) else None
        assert isinstance(parent_id, str) and parent_id in locations, 'Unknown map parent: ' + str(parent_id)
        view_name, parent = locations[parent_id]
        assert not parent['record_id'] and parent['kind'] != 'record', 'Record cannot be a map parent'
        leaf = leaves.get(rid)
        if leaf is not None and leaf['parent'] == parent_id:
            continue
        changed_views.add(view_name)
        if leaf is not None:
            old_name, _ = locations[leaf['id']]
            changed_views.add(old_name)
            old_parent = locations[leaf['parent']][1]
            old_parent['children'].remove(leaf['id'])
            views[old_name]['nodes'].remove(leaf)
        else:
            node_id = 'record:' + rid
            assert node_id not in locations, 'Record leaf ID collision: ' + node_id
            leaf = {'id': node_id, 'label': record['title'], 'kind': 'record',
                    'record_id': rid, 'children': [], 'members': [rid]}
        leaf.update(parent=parent_id, color=parent['color'])
        parent['children'].append(leaf['id'])
        views[view_name]['nodes'].append(leaf)
        locations[leaf['id']] = (view_name, leaf)
        leaves[rid] = leaf
    # Validate even a no-op declaration, without changing pinned source order.
    for name, view in views.items():
        nodes = {n['id']: n for n in view['nodes']}
        active, visited = set(), set()

        def visit(identifier, depth):
            assert identifier in nodes, 'Unknown child map node: ' + identifier
            assert identifier not in active, 'Cycle in research map'
            assert identifier not in visited, 'Duplicate child in research map'
            node = nodes[identifier]
            active.add(identifier)
            members = [node['record_id']] if node['record_id'] else []
            assert not node['record_id'] or not node['children'], 'Record cannot have children'
            for child in node['children']:
                assert child in nodes and nodes[child]['parent'] == identifier, 'Inconsistent map parent'
                members.extend(visit(child, depth + 1))
            assert len(members) == len(set(members)), 'Duplicate member in research map'
            if name in changed_views:
                node['depth'] = depth
                # Retain historical member order wherever membership is unchanged.
                node['members'] = [r for r in node['members'] if r in members] + [r for r in members if r not in node['members']]
                if node['record_id']:
                    node.setdefault('x', 0)
                    node.setdefault('left', node['x'])
                    node.setdefault('right', node['x'])
            active.remove(identifier)
            visited.add(identifier)
            return members

        assert view['root'] in nodes and nodes[view['root']]['parent'] is None, 'Invalid map root'
        members = visit(view['root'], 0)
        assert visited == set(nodes), 'Unreachable or cyclic research map node'
        if name in changed_views:
            # Coordinates are a legacy view hint; keep bounds coherent after moves.
            def position(identifier, cursor):
                node = nodes[identifier]
                if not node['children']:
                    node.update(x=cursor, left=cursor, right=cursor)
                    return cursor + 1
                start = cursor
                for child in node['children']:
                    cursor = position(child, cursor)
                node.update(left=start, right=cursor - 1, x=(start + cursor - 1) / 2)
                return cursor
            position(view['root'], 0)
            view['record_count'] = len(members)
    return views, set(leaves)


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
    retired = retired_ids(ROOT)
    assert not set(current).intersection(retired), 'Draft record remains in published registry'
    missing = set(snapshot) - set(current)
    assert missing <= retired, 'Snapshot records missing without an explicit v2 withdrawal: ' + ', '.join(sorted(missing - retired))
    views, assigned = {}, set()
    for view, filename in [('solving', 'solving-hierarchy.json'), ('analytics', 'analytics-hierarchy.json')]:
        source = load(SOURCE / filename)
        nodes = []
        for original in source['nodes']:
            node = {k: copy.deepcopy(original[k]) for k in
                    ('id', 'parent', 'label', 'color', 'kind', 'children', 'record_id', 'members', 'depth', 'x', 'left', 'right')}
            if node['record_id']:
                rid = node['record_id']
                assert (rid in current or rid in retired) and rid in snapshot, rid
                assert rid not in assigned, rid
                assigned.add(rid)
                if rid in current:
                    node['label'] = current[rid]['title']
                node['draft_operation'] = original['operation_tag']
            nodes.append(node)
        ids = {n['id'] for n in nodes}
        assert len(ids) == len(nodes)
        assert all(n['parent'] in ids or n['parent'] is None for n in nodes)
        views[view] = {'root': nodes[0]['id'], 'title': source['report']['root_aim'],
                       'selection_rule': source['selection_rule'], 'nodes': nodes,
                       'record_count': len(nodes[0]['members']), 'classification_status': 'draft'}
    views, assigned = place_classified(views, current, retired)
    records = {}
    for rid, record in sorted(current.items()):
        fields = provenance['snapshot_fields_sha256'].get(rid, {})
        changed = sorted(k for k in record
                         if fields.get(k) != sha(canonical(record[k]))) if fields else []
        changed += sorted(set(fields) - set(record))
        records[rid] = {'id': rid, 'title': record['title'],
                        **{key: record[key] for key in ('reader_title', 'reader_intro', 'reader_question') if key in record},
                        'question': record.get('reader_question') or record['question'],
                        'finding': record.get('reader_finding') or record['finding'],
                        'limitations': record.get('reader_limit') or record['limitations'],
                        'pages': record['scope']['pages'], 'scope': record['scope'],
                        'outcome': record['outcome'], 'href': '#/experiments/' + rid,
                        'current_sha256': sha(canonical(record)),
                        'snapshot_sha256': snapshot.get(rid), 'changed_fields': changed,
                        'classification': 'authored' if record.get('classification') else 'draft' if rid in assigned else
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
            'awaiting_classification': sorted(set(current) - set(snapshot) - assigned)}


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
