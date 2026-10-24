"""Exact input projection, deterministic freshness and recipe-pin checks."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from build_local_run_inputs import ROOT, PAGE_IDS, OUTPUT, SCHEMA, build, render


class LocalRunInputsTests(unittest.TestCase):
    def fixture(self, directory):
        root = Path(directory)
        (root / 'data/pages').mkdir(parents=True)
        source = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))
        index = {'alphabet': source['alphabet'], 'pages': [{'id': p} for p in PAGE_IDS]}
        (root / 'data/index.json').write_text(json.dumps(index, ensure_ascii=False), encoding='utf-8')
        for n, identifier in enumerate(PAGE_IDS):
            page = {'id': identifier, 'raw': 'ᚠ-ᚢ  \r\n\tᚦ/\n$\n' + str(n), 'private_metadata': 'excluded'}
            if n == 1:
                page['reviewed_text'] = ''
            elif n == 2:
                page['reviewed_text'] = None
            elif n == 3:
                page['reviewed_text'] = 'ᚢ\r\nᚠ  '
            (root / 'data/pages' / (identifier + '.json')).write_text(
                json.dumps(page, ensure_ascii=False), encoding='utf-8')
        return root

    def test_actual_all_75_texts_and_alphabet_exact_minimal_projection(self):
        output = json.loads(render(ROOT))
        self.assertEqual(set(output), {'schema', 'alphabet', 'pages'})
        self.assertEqual(output['schema'], SCHEMA)
        self.assertEqual([p['id'] for p in output['pages']], list(PAGE_IDS))
        index = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))
        self.assertEqual(output['alphabet'], [{k: a[k] for k in ('rune', 'latin', 'prime')} for a in index['alphabet']])
        for page in output['pages']:
            self.assertEqual(set(page), {'id', 'raw', 'reviewed_text'})
            source = json.loads((ROOT / 'data/pages' / (page['id'] + '.json')).read_text(encoding='utf-8'))
            self.assertEqual(page['raw'], source['raw'])
            self.assertEqual(page['reviewed_text'], source.get('reviewed_text'))
            self.assertEqual(hashlib.sha256(page['raw'].encode()).digest(),
                             hashlib.sha256(source['raw'].encode()).digest())

    def test_whitespace_null_missing_empty_reviewed_remain_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            pages = json.loads(render(root))['pages']
            self.assertEqual(pages[0]['raw'], 'ᚠ-ᚢ  \r\n\tᚦ/\n$\n0')
            self.assertIsNone(pages[0]['reviewed_text'])
            self.assertEqual(pages[1]['reviewed_text'], '')
            self.assertIsNone(pages[2]['reviewed_text'])
            self.assertEqual(pages[3]['reviewed_text'], 'ᚢ\r\nᚠ  ')

    def test_deterministic_compact_write_and_check_never_repairs_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            with self.assertRaisesRegex(ValueError, 'missing or stale'):
                build(root, check=True)
            first = build(root)
            self.assertEqual(first, build(root))
            self.assertEqual(first, build(root, check=True))
            self.assertLess(len(first), 2_000_000)
            self.assertNotIn(b'\\u16', first)
            self.assertEqual(first.count(b'\n'), 1)
            path = root / OUTPUT
            path.write_bytes(first + b' ')
            with self.assertRaisesRegex(ValueError, 'missing or stale'):
                build(root, check=True)
            self.assertEqual(path.read_bytes(), first + b' ')
            build(root)
            self.assertEqual(path.read_bytes(), first)

    def test_changed_source_requires_regeneration_without_text_normalization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            before = build(root)
            path = root / 'data/pages/lp2-15.json'
            page = json.loads(path.read_text(encoding='utf-8'))
            page['raw'] += '\r\n'
            path.write_text(json.dumps(page), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'stale'):
                build(root, check=True)
            after = build(root)
            self.assertNotEqual(before, after)
            self.assertEqual(next(p['raw'] for p in json.loads(after)['pages'] if p['id'] == 'lp2-15'), page['raw'])

    def test_invalid_index_page_or_reviewed_value_rejected(self):
        for alteration in ('duplicate', 'order', 'page-id', 'raw', 'reviewed'):
            with tempfile.TemporaryDirectory() as directory:
                root = self.fixture(directory)
                if alteration in ('duplicate', 'order'):
                    path = root / 'data/index.json'
                    value = json.loads(path.read_text(encoding='utf-8'))
                    if alteration == 'duplicate':
                        value['pages'][0] = value['pages'][1]
                    else:
                        value['pages'].reverse()
                else:
                    path = root / 'data/pages/lp2-15.json'
                    value = json.loads(path.read_text(encoding='utf-8'))
                    value[{'page-id': 'id', 'raw': 'raw', 'reviewed': 'reviewed_text'}[alteration]] = 17
                path.write_text(json.dumps(value), encoding='utf-8')
                with self.assertRaises(ValueError):
                    render(root)

    def test_authored_followup_text_and_alphabet_pins_still_match(self):
        aggregate = json.loads(render(ROOT))
        recipe = json.loads((ROOT / 'experiments/records/lp2-known-vigenere-keys/record.json').read_text(encoding='utf-8'))['browser_followups'][0]
        alphabet = json.dumps(aggregate['alphabet'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(hashlib.sha256(alphabet).hexdigest(), recipe['inputs']['alphabet_sha256'])
        lookup = {p['id']: p for p in aggregate['pages']}
        for pin in recipe['inputs']['pages']:
            self.assertEqual(hashlib.sha256(lookup[pin['id']]['raw'].encode()).hexdigest(), pin['text_sha256'])

    def test_oversized_input_cannot_produce_unbounded_runtime_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            path = root / 'data/pages/lp2-15.json'
            page = json.loads(path.read_text(encoding='utf-8'))
            page['raw'] = 'ᚠ' * 700000
            path.write_text(json.dumps(page, ensure_ascii=False), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'below 2 MB'):
                build(root)
            self.assertFalse((root / OUTPUT).exists())


if __name__ == '__main__':
    unittest.main()
