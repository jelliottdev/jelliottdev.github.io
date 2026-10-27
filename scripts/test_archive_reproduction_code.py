"""Invented code bytes only: retention never executes source or changes science."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
import archive_reproduction_code as A


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.put(A.POLICY, (A.ROOT / A.POLICY).read_bytes())
        self.code = 'scripts/retained_program_output.mjs'
        self.original = b'// invented retained helper\r\nconst x = "\xe1\x9a\xa0";\r\n'
        self.put(self.code, self.original)
        self.record('first', self.code, A.sha(self.original))

    def put(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def record(self, identifier, path, digest, **extra):
        value = {'id': identifier, 'status': 'published', 'reproduction': {
            'inputs': [{'path': path, 'sha256': digest}], 'outputs': []}}
        value.update(extra)
        self.put('experiments/records/' + identifier + '/record.json', json.dumps(value).encode())
        return value

    def write_manifest(self, value):
        self.put(A.MANIFEST, json.dumps(value).encode())

    def test_raw_versions_shared_associations_and_stale_missing_current(self):
        self.record('second', self.code, A.sha(self.original))
        first = A.build(self.root, write=True)
        self.assertEqual(len(first['entries']), 1)
        item = first['entries'][0]
        self.assertEqual(A.read_entry(self.root, item), self.original)
        self.assertEqual(A.build(self.root), first)
        updated = b'// independent next implementation\n'
        self.put(self.code, updated)
        self.assertEqual(A.build(self.root), first, 'Stale current code uses only retained exact bytes')
        self.record('second', self.code, A.sha(updated))
        with self.assertRaisesRegex(ValueError, 'stale'):
            A.build(self.root)
        second = A.build(self.root, write=True, baseline=first)
        self.assertEqual(len(second['entries']), 2)
        (self.root / self.code).unlink()
        self.assertEqual(A.build(self.root, baseline=first), second)
        self.assertEqual(A.read_entry(self.root, item), self.original)

    def test_unretained_stale_version_never_guessed_and_science_never_archived(self):
        self.put(self.code, b'// different current version\n')
        with self.assertRaisesRegex(ValueError, 'No exact retained'):
            A.build(self.root, write=True)
        self.assertFalse((self.root / A.MANIFEST).exists())
        self.record('first', 'experiments/records/first/results.json', 'a' * 64)
        self.assertEqual(A.build(self.root, write=True)['entries'], [])

    def test_corrupt_missing_orphan_and_append_only_baseline(self):
        value = A.build(self.root, write=True)
        item = value['entries'][0]
        archive = self.root / item['path']
        archive.write_bytes(b'corruption')
        with self.assertRaisesRegex(ValueError, 'changed'):
            A.build(self.root, write=True)
        self.assertEqual(archive.read_bytes(), b'corruption')
        archive.unlink()
        with self.assertRaises(FileNotFoundError):
            A.build(self.root)
        self.put(item['path'], self.original)
        self.write_manifest({'schema': A.SCHEMA, 'entries': []})
        with self.assertRaisesRegex(ValueError, 'removed or changed'):
            A.build(self.root, baseline=value)
        self.record('first', 'experiments/records/first/results.json', 'a' * 64)
        with self.assertRaisesRegex(ValueError, 'missing from retention'):
            A.build(self.root)

    def test_strict_policy_manifest_pins_and_bounds(self):
        value = A.build(self.root, write=True)
        for mutate in [lambda v: v['entries'].append(copy.deepcopy(v['entries'][0])),
                       lambda v: v['entries'][0].update(sourcePath='experiments/records/first/results.json'),
                       lambda v: v['entries'][0].update(path='../escape.js'),
                       lambda v: v['entries'][0].update(bytes=True),
                       lambda v: v['entries'][0].update(bytes=A.MAX_SOURCE + 1),
                       lambda v: v['entries'][0].update(sha256='a' * 64 + '\n')]:
            bad = copy.deepcopy(value)
            mutate(bad)
            with self.assertRaises(ValueError):
                A.manifest_entries(bad)
        policy = {'schema': 'liberpedia-maintained-reproduction-code-policy-v1',
                  'paths': list(A.policy(self.root)) + ['experiments/records/first/results.json']}
        self.put(A.POLICY, json.dumps(policy).encode())
        with self.assertRaisesRegex(ValueError, 'policy'):
            A.build(self.root)
        self.put(A.POLICY, (A.ROOT / A.POLICY).read_bytes())
        record = self.record('first', self.code, A.sha(self.original))
        record['reproduction']['inputs'].append(record['reproduction']['inputs'][0])
        self.put('experiments/records/first/record.json', json.dumps(record).encode())
        with self.assertRaisesRegex(ValueError, 'Repeated'):
            A.prepare(self.root)
        with self.assertRaisesRegex(ValueError, 'Repeated JSON'):
            A.parse(b'{"schema":1,"schema":2}')
        entries = [A.entry(self.code, str(i).encode() + b'x') for i in range(17)]
        for entry in entries:
            entry['bytes'] = A.MAX_SOURCE
        with self.assertRaisesRegex(ValueError, 'total byte'):
            A.manifest_entries({'schema': A.SCHEMA, 'entries': entries})

    def test_script_pin_duplicate_consistency_and_draft_exclusion(self):
        record = self.record('first', self.code, A.sha(self.original))
        record['reproduction'].update(script=self.code, script_sha256=A.sha(self.original))
        self.put('experiments/records/first/record.json', json.dumps(record).encode())
        self.assertEqual(len(A.build(self.root, write=True)['entries']), 1)
        record['reproduction']['script_sha256'] = '0' * 64
        self.put('experiments/records/first/record.json', json.dumps(record).encode())
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            A.prepare(self.root)
        record['status'] = 'draft'
        self.put('experiments/records/first/record.json', json.dumps(record).encode())
        self.assertEqual(len(A.build(self.root)['entries']), 1, 'Withdrawals never evict retained code')

    def test_admin_policy_extension_and_retained_membership(self):
        first = A.build(self.root, write=True)
        policy = {'schema': 'liberpedia-maintained-reproduction-code-policy-v1',
                  'paths': list(A.policy(self.root)) + ['scripts/future_shared.mjs']}
        self.put(A.POLICY, json.dumps(policy).encode())
        self.put('scripts/future_shared.mjs', b'// invented future shared implementation\n')
        self.record('future', 'scripts/future_shared.mjs', A.sha(b'// invented future shared implementation\n'))
        second = A.build(self.root, write=True, baseline=first)
        self.assertEqual(len(second['entries']), 2)
        policy['paths'].remove(self.code)
        self.put(A.POLICY, json.dumps(policy).encode())
        with self.assertRaisesRegex(ValueError, 'removed from policy'):
            A.prepare(self.root, baseline=first)

    def test_symlink_escape_and_association_cannot_authorize_other_path(self):
        value = A.build(self.root, write=True)
        wrong = copy.deepcopy(value['entries'][0])
        wrong['sourcePath'] = 'scripts/retained_program_collection.mjs'
        # Same extension is insufficient: absence of exact manifest association
        # is exposed by tuple keys for the caller's resolver to enforce.
        entries = A.manifest_entries(value)
        self.assertNotIn((wrong['sourcePath'], wrong['sha256']), entries)
        with tempfile.TemporaryDirectory() as outside:
            archive = self.root / value['entries'][0]['path']
            archive.unlink()
            external = Path(outside) / 'outside.mjs'
            external.write_bytes(self.original)
            try:
                archive.symlink_to(external)
            except OSError:
                self.skipTest('Symlink permission unavailable')
            with self.assertRaisesRegex(ValueError, 'escapes'):
                A.build(self.root)


if __name__ == '__main__':
    unittest.main()
