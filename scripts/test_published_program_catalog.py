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
        self.assertEqual(len(value['entries']), 74)
        self.assertEqual(sources, before)
        old = (catalog.ROOT / catalog.PROVIDERS[0]).read_bytes()
        self.assertEqual(catalog.prepare()['data/published-program-source-catalog.json'], catalog.stable(value) + '\n')
        self.assertEqual((catalog.ROOT / catalog.PROVIDERS[0]).read_bytes(), old)

    def test_duplicates_replacements_and_malformed_providers_reject(self):
        source = json.loads((catalog.ROOT / catalog.PROVIDERS[0]).read_bytes())
        first = source['entries'][0]
        for entry in (copy.deepcopy(first), {**first, 'revision': '0' * 64}):
            with self.assertRaisesRegex(ValueError, 'overlap'):
                catalog.merge([source, {'schema': catalog.SCHEMA, 'entries': [entry]}])
        for source in ({}, {'schema': 'other', 'entries': []}, {'schema': catalog.SCHEMA, 'entries': [{}]}):
            with self.assertRaises(ValueError):
                catalog.merge([source])

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
