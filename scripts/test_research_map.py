"""Data invariants for the optional maps; no browser or build dependencies."""
import importlib.util
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/build_research_map.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ResearchMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = builder.build()
        cls.registry = {r['id']: r for r in builder.load(ROOT / 'data/experiments.json')['records'] if r['status'] == 'published'}

    def test_legacy_trees_retain_exact_pinned_membership_and_parentage(self):
        # Explicit authored placements are tested separately; absence of them
        # must preserve every pinned hierarchy field, even after later imports.
        registry = builder.load(ROOT / 'data/experiments.json')
        for record in registry['records']:
            record.pop('classification', None)
        original_load = builder.load
        with patch.object(builder, 'load', side_effect=lambda path:
                          registry if path == ROOT / 'data/experiments.json' else original_load(path)):
            data = builder.build()
        assigned = set()
        for name, view in data['views'].items():
            original = builder.load(builder.SOURCE / (name + '-hierarchy.json'))
            nodes = {n['id']: n for n in view['nodes']}
            self.assertEqual(set(nodes), {n['id'] for n in original['nodes']})
            for old in original['nodes']:
                new = nodes[old['id']]
                for field in ['parent', 'children', 'members', 'x', 'left', 'right']:
                    self.assertEqual(new[field], old[field], (name, old['id'], field))
                seen = set()
                cursor = new
                while cursor['parent']:
                    self.assertNotIn(cursor['id'], seen)
                    seen.add(cursor['id'])
                    cursor = nodes[cursor['parent']]
                self.assertEqual(cursor['id'], view['root'])
                if new['record_id']:
                    self.assertNotIn(new['record_id'], assigned)
                    assigned.add(new['record_id'])
                    self.assertEqual(new['label'], self.registry[new['record_id']]['title'])
            self.assertEqual(set(nodes[view['root']]['members']), {n['record_id'] for n in nodes.values() if n['record_id']})
        self.assertEqual(assigned | set(data['outside_selected_views']) | set(data['awaiting_classification']), set(self.registry))

    def test_current_content_and_unclassified_remainder_are_exact(self):
        source = builder.load(builder.SOURCE / 'provenance.json')['snapshot_record_sha256']
        assigned = {n['record_id'] for v in self.data['views'].values() for n in v['nodes'] if n['record_id']}
        self.assertEqual(self.data['awaiting_classification'], sorted(set(self.registry) - set(source) - assigned))
        self.assertEqual(self.data['provenance']['missing_snapshot_ids'],
                         sorted(set(source) - set(self.registry)))
        self.assertLessEqual(set(self.data['provenance']['missing_snapshot_ids']), builder.retired_ids(ROOT))
        for rid, record in self.registry.items():
            mapped = self.data['records'][rid]
            self.assertEqual(mapped['current_sha256'], builder.sha(builder.canonical(record)))
            self.assertEqual(mapped['finding'], record.get('reader_finding') or record['finding'])
            self.assertEqual(mapped['scope'], record['scope'])
            self.assertEqual(mapped['href'], '#/experiments/' + rid)
            if record.get('classification'):
                self.assertEqual(mapped['classification'], 'authored')
            elif rid not in source:
                self.assertEqual(mapped['classification'], 'awaiting-classification')
            if rid in source:
                self.assertEqual(bool(mapped['changed_fields']), source[rid] != mapped['current_sha256'])

    def test_output_is_deterministic_and_current(self):
        expected=(json.dumps(self.data, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
        self.assertEqual((ROOT / 'data/research-map.json').read_bytes(), expected)
        self.assertEqual(builder.canonical(builder.build()), builder.canonical(self.data))

    def test_registry_comparison_metadata_refreshes_provenance_without_changing_hierarchy(self):
        registry = builder.load(ROOT / 'data/experiments.json')
        record = next(r for r in registry['records'] if r.get('recorded_comparison'))
        rid = record['id']
        record['recorded_comparison']['input_description'] += ' Isolated test fixture.'
        with tempfile.TemporaryDirectory(prefix='research-map-registry-') as temporary:
            root = Path(temporary)
            (root / 'data').mkdir()
            raw = (json.dumps(registry, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
            (root / 'data/experiments.json').write_bytes(raw)
            # Keep the original pinned handoff; only the current registry changes.
            with patch.object(builder, 'ROOT', root):
                updated = builder.build()
        self.assertEqual(updated['provenance']['current_experiments_sha256'], builder.sha(raw))
        self.assertNotEqual(updated['provenance']['current_experiments_sha256'],
                            self.data['provenance']['current_experiments_sha256'])
        self.assertEqual(updated['records'][rid]['current_sha256'], builder.sha(builder.canonical(record)))
        self.assertNotEqual(updated['records'][rid]['current_sha256'], self.data['records'][rid]['current_sha256'])
        self.assertIn('recorded_comparison', updated['records'][rid]['changed_fields'])
        self.assertEqual(updated['views'], self.data['views'])
        self.assertEqual(updated['awaiting_classification'], self.data['awaiting_classification'])
        self.assertEqual(updated['outside_selected_views'], self.data['outside_selected_views'])

    def test_same_parent_classification_preserves_every_hierarchy_byte(self):
        current = copy.deepcopy(self.registry)
        current['cumulative-autokey-literal']['classification'] = {
            'kind': 'method', 'methods': ['feedback'], 'map_parent': 'method:feedback'}
        before = copy.deepcopy(self.data['views'])
        views, assigned = builder.place_classified(before, current)
        self.assertEqual(views, before)
        self.assertIn('cumulative-autokey-literal', assigned)
        self.assertEqual(before, self.data['views'], 'Placement must not mutate caller data')

    def test_explicit_new_record_is_added_once_and_legacy_remainder_stays_out(self):
        current = copy.deepcopy(self.registry)
        current['new-authored-record'] = {
            'title': 'Exact new record', 'classification': {
                'kind': 'method', 'methods': ['feedback'], 'map_parent': 'method:feedback'}}
        current['new-legacy-record'] = {'title': 'No inferred placement'}
        before = copy.deepcopy(self.data['views'])
        views, assigned = builder.place_classified(before, current)
        nodes = {n['id']: n for n in views['solving']['nodes']}
        leaf = nodes['record:new-authored-record']
        self.assertEqual(leaf['parent'], 'method:feedback')
        self.assertEqual(leaf['label'], 'Exact new record')
        self.assertEqual(leaf['color'], nodes['method:feedback']['color'])
        self.assertEqual(nodes['method:feedback']['children'].count(leaf['id']), 1)
        self.assertEqual(nodes['method:feedback']['members'].count('new-authored-record'), 1)
        self.assertIn('new-authored-record', nodes[views['solving']['root']]['members'])
        self.assertEqual(views['solving']['record_count'], before['solving']['record_count'] + 1)
        self.assertEqual(views['analytics'], before['analytics'])
        self.assertNotIn('new-legacy-record', assigned)
        self.assertEqual(before, self.data['views'])
        again, _ = builder.place_classified(views, current)
        self.assertEqual(again, views, 'Repeated reconciliation must not duplicate the leaf')

    def test_explicit_move_between_views_updates_members_depth_and_old_parent(self):
        current = copy.deepcopy(self.registry)
        current['cumulative-autokey-literal']['classification'] = {
            'kind': 'method', 'methods': ['feedback'], 'map_parent': 'method:language'}
        before = copy.deepcopy(self.data['views'])
        views, assigned = builder.place_classified(before, current)
        rid = 'cumulative-autokey-literal'
        all_nodes = {n['id']: n for view in views.values() for n in view['nodes']}
        self.assertEqual(all_nodes['record:' + rid]['parent'], 'method:language')
        self.assertEqual(all_nodes['record:' + rid]['depth'], all_nodes['method:language']['depth'] + 1)
        self.assertNotIn('record:' + rid, all_nodes['method:feedback']['children'])
        self.assertNotIn(rid, all_nodes['method:feedback']['members'])
        self.assertIn(rid, all_nodes['method:language']['members'])
        self.assertEqual(sum(n.get('record_id') == rid for v in views.values() for n in v['nodes']), 1)
        self.assertEqual(views['solving']['record_count'], before['solving']['record_count'] - 1)
        self.assertEqual(views['analytics']['record_count'], before['analytics']['record_count'] + 1)
        self.assertIn(rid, assigned)

    def test_invalid_parents_ambiguous_nodes_and_cycles_reject_without_mutation(self):
        current = copy.deepcopy(self.registry)
        for parent in ('missing-parent', 'record:cumulative-autokey-literal', None):
            with self.subTest(parent=parent):
                current['cumulative-autokey-literal']['classification'] = {'map_parent': parent}
                before = copy.deepcopy(self.data['views'])
                with self.assertRaises(AssertionError):
                    builder.place_classified(before, current)
                self.assertEqual(before, self.data['views'])
        current = copy.deepcopy(self.registry)
        duplicate = copy.deepcopy(self.data['views'])
        duplicate['analytics']['nodes'].append(copy.deepcopy(duplicate['solving']['nodes'][0]))
        with self.assertRaisesRegex(AssertionError, 'Ambiguous'):
            builder.place_classified(duplicate, current)
        cycle = copy.deepcopy(self.data['views'])
        nodes = {n['id']: n for n in cycle['solving']['nodes']}
        nodes['method:feedback']['children'].append(cycle['solving']['root'])
        with self.assertRaises(AssertionError):
            builder.place_classified(cycle, current)

    def test_explicit_classification_build_removes_only_authored_new_id_from_remainder(self):
        registry = builder.load(ROOT / 'data/experiments.json')
        original = copy.deepcopy(registry['records'][0])
        original.update(id='new-explicit-placement', title='New explicit placement',
                        classification={'kind': 'method', 'methods': ['feedback'],
                                        'map_parent': 'method:feedback'})
        registry['records'].append(original)
        with tempfile.TemporaryDirectory(prefix='research-map-placement-') as temporary:
            root = Path(temporary)
            (root / 'data').mkdir()
            (root / 'data/experiments.json').write_text(json.dumps(registry), encoding='utf-8')
            with patch.object(builder, 'ROOT', root):
                updated = builder.build()
        self.assertEqual(updated['awaiting_classification'], self.data['awaiting_classification'])
        self.assertEqual(updated['outside_selected_views'], self.data['outside_selected_views'])
        self.assertEqual(updated['records']['new-explicit-placement']['classification'], 'authored')
        self.assertIn('new-explicit-placement', updated['provenance']['new_ids'])

    def test_build_withdrawal_and_republication_restore_pinned_and_authored_placement(self):
        registry = builder.load(ROOT / 'data/experiments.json')
        rid = 'cumulative-autokey-literal'
        record = copy.deepcopy(next(r for r in registry['records'] if r['id'] == rid))
        source_pins = {name: (builder.SOURCE / name).read_bytes()
                       for name in ('provenance.json', 'solving-hierarchy.json', 'analytics-hierarchy.json')}
        with tempfile.TemporaryDirectory(prefix='research-map-withdrawal-') as temporary:
            root = Path(temporary)
            (root / 'data').mkdir()
            folder = root / 'experiments/records' / rid
            folder.mkdir(parents=True)
            canonical = {'schema': builder.SCHEMA, 'id': rid, 'status': 'draft',
                         'classification': {'kind': 'method', 'methods': ['feedback'],
                                            'map_parent': 'method:language'}}
            path = folder / 'record.json'
            path.write_text(json.dumps(canonical), encoding='utf-8')
            registry['records'] = [r for r in registry['records'] if r['id'] != rid]
            registry_path = root / 'data/experiments.json'
            registry_path.write_text(json.dumps(registry), encoding='utf-8')
            canonical_before = path.read_bytes()
            with patch.object(builder, 'ROOT', root):
                withdrawn = builder.build()
            self.assertNotIn(rid, withdrawn['records'])
            self.assertEqual(withdrawn['provenance']['missing_snapshot_ids'], [rid])
            for view in withdrawn['views'].values():
                self.assertFalse(any(n['record_id'] == rid for n in view['nodes']))
                self.assertTrue(all(rid not in n['members'] and 'record:' + rid not in n['children'] for n in view['nodes']))
                nodes = {n['id']: n for n in view['nodes']}
                self.assertEqual(view['record_count'], len(nodes[view['root']]['members']))
                self.assertTrue(all(n['left'] <= n['x'] <= n['right'] for n in view['nodes']))
            self.assertEqual(path.read_bytes(), canonical_before, 'Map build never edits canonical source')
            self.assertEqual(withdrawn['views']['analytics'], self.data['views']['analytics'])
            # Republishing without an override restores the original pinned leaf.
            canonical['status'] = 'published'
            path.write_text(json.dumps(canonical), encoding='utf-8')
            registry['records'].append(record)
            registry_path.write_text(json.dumps(registry), encoding='utf-8')
            with patch.object(builder, 'ROOT', root):
                restored = builder.build()
            self.assertEqual(restored['views'], self.data['views'])
            self.assertEqual(restored['provenance']['missing_snapshot_ids'], [])
            # An explicit republished classification can instead move the leaf.
            record['classification'] = canonical['classification']
            registry_path.write_text(json.dumps(registry), encoding='utf-8')
            with patch.object(builder, 'ROOT', root):
                moved = builder.build()
            leaf = next(n for n in moved['views']['analytics']['nodes'] if n['record_id'] == rid)
            self.assertEqual(leaf['parent'], 'method:language')
            self.assertNotIn(rid, moved['views']['solving']['nodes'][0]['members'])
        for name, raw in source_pins.items():
            self.assertEqual((builder.SOURCE / name).read_bytes(), raw)

    def test_missing_legacy_or_unapproved_source_record_still_rejects(self):
        rid = 'cumulative-autokey-literal'
        registry = builder.load(ROOT / 'data/experiments.json')
        registry['records'] = [r for r in registry['records'] if r['id'] != rid]
        with tempfile.TemporaryDirectory(prefix='research-map-unapproved-') as temporary:
            root = Path(temporary)
            (root / 'data').mkdir()
            (root / 'data/experiments.json').write_text(json.dumps(registry), encoding='utf-8')
            folder = root / 'experiments/records' / rid
            folder.mkdir(parents=True)
            for raw in ({'id': rid, 'status': 'draft'},
                        {'id': rid, 'schema': builder.SCHEMA, 'status': 'published'}):
                (folder / 'record.json').write_text(json.dumps(raw), encoding='utf-8')
                with self.subTest(raw=raw), patch.object(builder, 'ROOT', root), self.assertRaisesRegex(AssertionError, 'without an explicit v2 withdrawal'):
                    builder.build()
            (folder / 'record.json').write_text(json.dumps({'id': rid, 'schema': builder.SCHEMA, 'status': 'draft'}), encoding='utf-8')
            original = copy.deepcopy(self.registry[rid])
            registry['records'].append(original)
            (root / 'data/experiments.json').write_text(json.dumps(registry), encoding='utf-8')
            with patch.object(builder, 'ROOT', root), self.assertRaisesRegex(AssertionError, 'Draft record remains'):
                builder.build()

    def test_retirement_requires_safe_matching_canonical_id(self):
        with tempfile.TemporaryDirectory(prefix='research-map-retired-id-') as temporary:
            root = Path(temporary)
            folder = root / 'experiments/records/safe-folder'
            folder.mkdir(parents=True)
            for rid in ('../escape', 'another-folder', None):
                (folder / 'record.json').write_text(json.dumps({'id': rid, 'schema': builder.SCHEMA, 'status': 'draft'}), encoding='utf-8')
                with self.subTest(rid=rid), self.assertRaises((AssertionError, ValueError)):
                    builder.retired_ids(root)

    def test_withdrawn_post_snapshot_record_disappears_without_changing_source_provenance(self):
        registry = builder.load(ROOT / 'data/experiments.json')
        record = copy.deepcopy(registry['records'][0])
        rid = 'new-withdrawal-fixture'
        record.update(id=rid, classification={'kind': 'method', 'methods': ['feedback'], 'map_parent': 'method:feedback'})
        with tempfile.TemporaryDirectory(prefix='research-map-new-withdrawal-') as temporary:
            root = Path(temporary)
            (root / 'data').mkdir()
            path = root / 'data/experiments.json'
            path.write_text(json.dumps({**registry, 'records': registry['records'] + [record]}), encoding='utf-8')
            with patch.object(builder, 'ROOT', root):
                published = builder.build()
            self.assertIn(rid, published['records'])
            folder = root / 'experiments/records' / rid
            folder.mkdir(parents=True)
            (folder / 'record.json').write_text(json.dumps({'id': rid, 'schema': builder.SCHEMA, 'status': 'draft'}), encoding='utf-8')
            path.write_text(json.dumps(registry), encoding='utf-8')
            with patch.object(builder, 'ROOT', root):
                withdrawn = builder.build()
            self.assertNotIn(rid, withdrawn['records'])
            self.assertEqual(withdrawn['views'], self.data['views'])
            self.assertEqual(withdrawn['provenance']['missing_snapshot_ids'], self.data['provenance']['missing_snapshot_ids'])
            self.assertEqual(withdrawn['provenance']['source_files'], self.data['provenance']['source_files'])


if __name__ == '__main__':
    unittest.main()
