"""Data invariants for the optional maps; no browser or build dependencies."""
import importlib.util
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

    def test_disjoint_trees_retain_exact_pinned_membership_and_parentage(self):
        assigned = set()
        for name, view in self.data['views'].items():
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
        self.assertEqual(assigned | set(self.data['outside_selected_views']) | set(self.data['awaiting_classification']), set(self.registry))

    def test_current_content_and_unclassified_remainder_are_exact(self):
        source = builder.load(builder.SOURCE / 'provenance.json')['snapshot_record_sha256']
        self.assertEqual(self.data['awaiting_classification'], sorted(set(self.registry) - set(source)))
        self.assertFalse(self.data['provenance']['missing_snapshot_ids'])
        for rid, record in self.registry.items():
            mapped = self.data['records'][rid]
            self.assertEqual(mapped['current_sha256'], builder.sha(builder.canonical(record)))
            self.assertEqual(mapped['finding'], record.get('reader_finding') or record['finding'])
            self.assertEqual(mapped['scope'], record['scope'])
            self.assertEqual(mapped['href'], '#/experiments/' + rid)
            if rid not in source:
                self.assertEqual(mapped['classification'], 'awaiting-classification')
            else:
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


if __name__ == '__main__':
    unittest.main()
