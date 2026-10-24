"""Hash refresh preserves authored v2 content and never materializes accounts."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from experiment_content import SCHEMA
from refresh_experiment_hashes import refresh


def sha(data):
    return hashlib.sha256(data).hexdigest()


class RefreshHashesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='experiment-hash-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.prefix = 'experiments/records/fixture/'
        self.folder = self.root / self.prefix
        self.folder.mkdir(parents=True)
        self.path = self.folder / 'record.json'
        (self.folder / 'run.py').write_bytes(b'# frozen script\n')
        (self.folder / 'result.json').write_bytes(b'{"measured": 7}\n')
        self.record = {
            'id': 'fixture', 'schema': SCHEMA, 'status': 'draft',
            'result': {'finding': 'A measured result.', 'limits': 'A fixed scope.',
                       'next_steps': 'Retain the evidence.'},
            'analysis': '# Account\r\n\r\nRune \u16a0 and score \u2212 2.\r\n',
            'reproduction': {
                'script': self.prefix + 'run.py',
                'script_sha256': sha((self.folder / 'run.py').read_bytes()),
                'inputs': [{'path': self.prefix + 'article.md', 'sha256': '0' * 64}],
                'outputs': [{'path': self.prefix + 'result.json',
                             'sha256': sha((self.folder / 'result.json').read_bytes())}],
            },
        }
        self.save()

    def save(self):
        self.path.write_bytes((json.dumps(self.record, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

    def test_v2_check_hashes_virtual_account_without_writing_any_file(self):
        before = self.path.read_bytes()
        self.assertEqual(refresh(self.root, 'fixture'), [self.prefix + 'article.md'])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse((self.folder / 'article.md').exists())
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()),
                         ['record.json', 'result.json', 'run.py'])

    def test_v2_write_updates_only_declared_hash_preserving_analysis_bytes(self):
        before = copy.deepcopy(self.record)
        changes = refresh(self.root, 'fixture', write=True)
        after = json.loads(self.path.read_bytes())
        self.assertEqual(changes, [self.prefix + 'article.md'])
        expected = copy.deepcopy(before)
        expected['reproduction']['inputs'][0]['sha256'] = sha(before['analysis'].encode('utf-8'))
        self.assertEqual(after, expected)
        self.assertFalse((self.folder / 'article.md').exists())
        self.assertEqual(refresh(self.root, 'fixture'), [])
        self.assertNotEqual(expected['reproduction']['inputs'][0]['sha256'],
                            sha(before['analysis'].replace('\r\n', '\n').encode('utf-8')))

    def test_v2_stale_disk_account_ignored_in_both_roles_and_not_overwritten(self):
        stale = b'An obsolete derived account.\n'
        (self.folder / 'article.md').write_bytes(stale)
        self.record['reproduction']['inputs'][0]['sha256'] = sha(stale)
        self.record['reproduction']['outputs'].append(
            {'path': self.prefix + 'article.md', 'sha256': sha(stale)})
        self.save()
        self.assertEqual(refresh(self.root, 'fixture', write=True),
                         [self.prefix + 'article.md', self.prefix + 'article.md'])
        refreshed = json.loads(self.path.read_bytes())['reproduction']
        expected = sha(self.record['analysis'].encode('utf-8'))
        self.assertEqual(refreshed['inputs'][0]['sha256'], expected)
        self.assertEqual(refreshed['outputs'][-1]['sha256'], expected)
        self.assertEqual((self.folder / 'article.md').read_bytes(), stale)

    def test_legacy_uses_disk_account_even_if_analysis_key_is_present(self):
        self.record.pop('schema')
        self.save()
        with self.assertRaises(ValueError):
            refresh(self.root, 'fixture')
        disk = b'Legacy account bytes.\r\n'
        (self.folder / 'article.md').write_bytes(disk)
        refresh(self.root, 'fixture', write=True)
        self.assertEqual(json.loads(self.path.read_bytes())['reproduction']['inputs'][0]['sha256'], sha(disk))

    def test_other_records_and_other_dependencies_never_use_virtual_account(self):
        other = self.root / 'experiments/records/other'
        other.mkdir()
        disk = b'A separate record account.\n'
        (other / 'article.md').write_bytes(disk)
        self.record['reproduction']['inputs'].append(
            {'path': 'experiments/records/other/article.md', 'sha256': sha(disk)})
        self.save()
        self.assertEqual(refresh(self.root, 'fixture'), [self.prefix + 'article.md'])
        (self.folder / 'result.json').unlink()
        with self.assertRaises(ValueError):
            refresh(self.root, 'fixture', write=True)
        self.assertEqual(json.loads(self.path.read_bytes()), self.record,
                         'A failed refresh must not partially write the record')

    def test_invalid_analysis_and_unsafe_dependencies_rejected_without_writes(self):
        for analysis in ('', None):
            with self.subTest(analysis=analysis):
                self.record['analysis'] = analysis
                self.save()
                before = self.path.read_bytes()
                with self.assertRaises(ValueError):
                    refresh(self.root, 'fixture', write=True)
                self.assertEqual(self.path.read_bytes(), before)
        self.record['analysis'] = 'Valid account.'
        self.record['reproduction']['inputs'][0]['path'] = '../escape/article.md'
        self.save()
        with self.assertRaises(ValueError):
            refresh(self.root, 'fixture', write=True)


if __name__ == '__main__':
    unittest.main()
