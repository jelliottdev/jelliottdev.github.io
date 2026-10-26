"""Exact-byte source retention, idempotence and monotonic history checks."""
import copy
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
import archive_authored_sources as archive


class SourceArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'experiments/records/fixture/record.json'
        self.path.parent.mkdir(parents=True)
        # Preserve formatting and CRLF as actual source evidence.
        self.original = b'{\r\n  "id":"fixture", "status":"published",\r\n  "browser_followups":[{"id":"first","kind":"finite-settings"}]\r\n}\r\n'
        self.path.write_bytes(self.original)

    def test_exact_bytes_idempotence_and_source_edits_preserve_all_revisions(self):
        manifest = archive.build(self.root, write=True)
        old = manifest['entries'][0]
        self.assertEqual((self.root / old['path']).read_bytes(), self.original)
        self.assertEqual(archive.build(self.root), manifest)
        self.assertEqual(archive.build(self.root, write=True), manifest)
        self.path.write_bytes(self.original.replace(b'"first"', b'"second"'))
        with self.assertRaisesRegex(ValueError, 'stale'):
            archive.build(self.root)
        current = archive.build(self.root, write=True, baseline=manifest)
        self.assertEqual(len(current['entries']), 2)
        self.assertEqual((self.root / old['path']).read_bytes(), self.original)
        self.assertEqual(archive.build(self.root, baseline=manifest), current)

    def test_tamper_deletion_and_coordinated_eviction_fail(self):
        original = archive.build(self.root, write=True)
        item = original['entries'][0]
        path = self.root / item['path']
        path.write_bytes(self.original + b' ')
        with self.assertRaisesRegex(ValueError, 'missing or changed'):
            archive.build(self.root, write=True)
        path.write_bytes(self.original)
        path.unlink()
        with self.assertRaisesRegex(ValueError, 'missing or changed'):
            archive.build(self.root)
        # An explicit CI baseline also rejects removal from the manifest.
        (self.root / archive.MANIFEST).write_text(json.dumps({'schema': original['schema'], 'entries': []}), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'removed or changed'):
            archive.build(self.root, baseline=original)

    def test_first_introduction_and_missing_current_manifest_have_distinct_baseline_rules(self):
        initial = archive.build(self.root, write=True)
        self.assertEqual(archive.build(self.root, baseline=None), initial)
        (self.root / archive.MANIFEST).unlink()
        with self.assertRaisesRegex(ValueError, 'removed or changed'):
            archive.build(self.root, baseline=initial)

    def test_complete_history_eviction_cannot_be_hidden_by_removing_its_current_record(self):
        initial = archive.build(self.root, write=True)
        self.path.unlink()
        (self.root / initial['entries'][0]['path']).unlink()
        (self.root / archive.MANIFEST).write_text(json.dumps({'schema': initial['schema'], 'entries': []}), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'removed or changed'):
            archive.build(self.root, baseline=initial)

    def test_exact_git_baseline_distinguishes_first_introduction_from_later_eviction(self):
        def git(*args, check=True):
            return subprocess.run(['git', '-C', str(self.root), *args], check=check, capture_output=True)
        (self.root / '.gitattributes').write_bytes((archive.ROOT / '.gitattributes').read_bytes())
        git('init')
        git('add', '.gitattributes', 'experiments')
        git('-c', 'user.name=Archive fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'Fixture before archive introduction')
        initial_base = git('rev-parse', 'HEAD').stdout.decode().strip()
        self.assertNotEqual(git('cat-file', '-e', initial_base + ':' + archive.MANIFEST, check=False).returncode, 0)
        first = archive.build(self.root, write=True)
        self.assertEqual(archive.build(self.root), first)
        git('add', archive.MANIFEST, archive.PREFIX)
        git('-c', 'user.name=Archive fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'Fixture immutable source baseline')
        exact_base = git('rev-parse', 'HEAD').stdout.decode().strip()
        baseline = archive.parse(git('show', exact_base + ':' + archive.MANIFEST).stdout)
        self.assertEqual(baseline, first)
        self.assertEqual(git('show', exact_base + ':' + first['entries'][0]['path']).stdout, self.original, 'Production Git attributes must preserve exact archived CRLF source bytes')
        (self.root / archive.MANIFEST).unlink()
        with self.assertRaisesRegex(ValueError, 'removed or changed'):
            archive.build(self.root, baseline=baseline)

    def test_ci_always_checks_retention_against_an_explicit_event_base_without_writing(self):
        workflow = (archive.ROOT / '.github/workflows/validate-experiments.yml').read_text(encoding='utf-8')
        block = workflow.split('      - name: Check current and retained authored source revisions', 1)[1].split('      - run:', 1)[0]
        self.assertNotIn('if: steps.scope.outputs.science', block)
        self.assertIn('github.event.pull_request.base.sha', block)
        self.assertIn('github.event.before', block)
        self.assertIn('git cat-file -e "$base^{commit}"', block)
        self.assertIn('git show "$base:$manifest" > "$baseline"', block)
        self.assertIn('--baseline-manifest "$baseline"', block)
        self.assertNotIn('--write', block)

    def test_unindexed_objects_and_malformed_manifest_fail(self):
        value = archive.build(self.root, write=True)
        (self.root / archive.PREFIX / ('0' * 64 + '.json')).write_bytes(self.original)
        with self.assertRaisesRegex(ValueError, 'missing from the retention manifest'):
            archive.build(self.root)
        changed = copy.deepcopy(value)
        changed['entries'][0]['path'] = '../outside.json'
        with self.assertRaises(ValueError):
            archive.manifest_entries(changed)

    def test_real_current_records_prepare_without_rewriting_or_publishing(self):
        files = archive.prepare()
        value = archive.parse(files[archive.MANIFEST])
        self.assertGreaterEqual(len(value['entries']), 1)
        for item in value['entries']:
            if item['path'] in files:
                source = archive.ROOT / 'experiments/records' / item['recordId'] / 'record.json'
                self.assertEqual(files[item['path']], source.read_bytes())
            else:
                self.assertEqual(archive.entry((archive.ROOT / item['path']).read_bytes()), item)


if __name__ == '__main__':
    unittest.main()
