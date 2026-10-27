import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
import build_published_program_catalog as catalog


class CatalogTests(unittest.TestCase):
    def test_current_providers_are_retained_in_order_without_mutation(self):
        sources = [json.loads((catalog.ROOT / name).read_bytes()) for name in catalog.PROVIDERS]
        before = copy.deepcopy(sources)
        value = catalog.merge(sources)
        self.assertEqual(value['entries'], [entry for source in sources for entry in source['entries']])
        self.assertEqual(catalog.PROVIDERS[:3], ('data/published-program-source-index.json', 'data/published-panel-program-source-index.json', 'data/published-numeric-program-source-index.json'))
        self.assertEqual(catalog.PROVIDERS[3:], ('data/published-declared-program-source-index.json',))
        historical = [entry for source in sources[:3] for entry in source['entries']]
        self.assertEqual(len(historical), 306)
        self.assertEqual(value['entries'][:306], historical)
        self.assertEqual(value['entries'][306:], sources[3]['entries'])
        self.assertEqual(value['entries'][:74], [entry for source in sources[:2] for entry in source['entries']])
        self.assertEqual(sources, before)
        old = [(catalog.ROOT / name).read_bytes() for name in catalog.PROVIDERS[:3]]
        self.assertEqual(catalog.prepare()['data/published-program-source-catalog.json'], catalog.stable(value) + '\n')
        self.assertEqual([(catalog.ROOT / name).read_bytes() for name in catalog.PROVIDERS[:3]], old)

    def test_new_declared_provider_flows_through_default_build_without_rewriting_history(self):
        sources = [json.loads((catalog.ROOT / name).read_bytes()) for name in catalog.PROVIDERS[:3]]
        entry = copy.deepcopy(sources[0]['entries'][0])
        entry.update(recordId='new-declared-record', caseId='new-declared-program', path='data/published-programs/new-declared-program.json')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in catalog.PROVIDERS[:3]:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((catalog.ROOT / name).read_bytes())
            path = root / catalog.PROVIDERS[3]
            path.write_text(catalog.stable({'schema': catalog.SCHEMA, 'entries': [entry]}), encoding='utf8')
            value = catalog.build(root, write=True)
            self.assertEqual(value['entries'][:-1], [e for source in sources for e in source['entries']])
            self.assertEqual(value['entries'][-1], entry)
            self.assertEqual(catalog.build(root), value)
            for name in catalog.PROVIDERS[:3]:
                self.assertEqual((root / name).read_bytes(), (catalog.ROOT / name).read_bytes())

    def test_duplicates_replacements_and_malformed_providers_reject(self):
        source = json.loads((catalog.ROOT / catalog.PROVIDERS[0]).read_bytes())
        first = source['entries'][0]
        for entry in (copy.deepcopy(first), {**first, 'revision': '0' * 64}):
            with self.assertRaisesRegex(ValueError, 'overlap'):
                catalog.merge([source, {'schema': catalog.SCHEMA, 'entries': [entry]}])
        for source in ({}, {'schema': 'other', 'entries': []}, {'schema': catalog.SCHEMA, 'entries': [{}]}):
            with self.assertRaises(ValueError):
                catalog.merge([source])

    def test_shared_matrix_paths_require_distinct_selectors_and_identical_source_binding(self):
        source = json.loads((catalog.ROOT / catalog.PROVIDERS[2]).read_bytes())
        self.assertEqual(len(source['entries']), 232)
        self.assertEqual(len({entry['path'] for entry in source['entries']}), 4)
        self.assertEqual(catalog.merge([source]), source)
        first = source['entries'][0]
        for mutate in (
            lambda value: value.update(revision='0' * 64),
            lambda value: value.update(programId='different-program', caseId='different-program--all-pages', sha256='0' * 64),
            lambda value: value.update(sourceFormat='unknown'),
            lambda value: value.update(bytes=True),
            lambda value: value.pop('programId'),
        ):
            changed = copy.deepcopy(first)
            mutate(changed)
            with self.assertRaises(ValueError):
                catalog.merge([source, {'schema': catalog.SCHEMA, 'entries': [changed]}])

    def test_bounded_catalog_drift_and_compiled_parity(self):
        value = catalog.build()
        self.assertEqual(value, json.loads((catalog.ROOT / 'data/published-program-source-catalog.json').read_bytes()))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in catalog.PROVIDERS:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((catalog.ROOT / name).read_bytes())
            with self.assertRaisesRegex(ValueError, 'stale'):
                catalog.build(root)
            self.assertEqual(catalog.build(root, write=True), value)
            self.assertEqual(catalog.build(root), value)
            path = root / 'data/published-program-source-catalog.json'
            path.write_bytes(path.read_bytes() + b' ')
            with self.assertRaisesRegex(ValueError, 'stale'):
                catalog.build(root)
        entry = {'recordId': 'r', 'revision': 'a', 'caseId': 'c', 'path': 'p', 'padding': 'x' * catalog.MAX_BYTES}
        with self.assertRaisesRegex(ValueError, 'byte bound'):
            catalog.merge([{'schema': catalog.SCHEMA, 'entries': [entry]}])


if __name__ == '__main__':
    unittest.main()
