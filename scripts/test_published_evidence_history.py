"""Append-only proof retention does not depend on Git after explicit bootstrap."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from build_published_evidence_history import ROOT, HISTORY, JAVASCRIPT, CURRENT, BUDGET, build, merge, stable


class HistoryTests(unittest.TestCase):
    def fixture(self):
        temp = tempfile.TemporaryDirectory(prefix='liberpedia-history-')
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        for name in [HISTORY, JAVASCRIPT, *CURRENT]:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        return root

    def test_current_artifacts_are_deterministic_and_normal_build_never_calls_git(self):
        root = self.fixture()
        self.assertFalse((root / '.git').exists())
        with patch('build_published_evidence_history.public_git_sources', side_effect=AssertionError('Normal builds must not use Git')):
            expected = build(write=False)
            self.assertEqual(build(root, write=False), expected)
            self.assertEqual(build(root), expected)
            self.assertEqual((root / HISTORY).read_bytes(), (ROOT / HISTORY).read_bytes())

    def test_missing_archive_cannot_silently_start_over(self):
        root = self.fixture()
        (root / HISTORY).unlink()
        with self.assertRaisesRegex(ValueError, 'bootstrap explicitly'):
            build(root)

    def test_current_only_manifests_never_remove_historical_envelopes(self):
        root = self.fixture()
        before = json.loads((root / HISTORY).read_bytes())
        result = build(root)
        self.assertEqual(result['receipts'], before['receipts'])
        self.assertEqual(len(result['tasks']), 2)
        self.assertEqual(len(result['results']), 2)

    def test_budget_failure_does_not_evict_receipts_or_touch_artifacts(self):
        root = self.fixture()
        before = {name: (root / name).read_bytes() for name in [HISTORY, JAVASCRIPT]}
        with patch.dict(BUDGET, {'receipts': 3}):
            with self.assertRaisesRegex(ValueError, 'no receipts may be evicted'):
                build(root)
        self.assertEqual({name: (root / name).read_bytes() for name in before}, before)

    def test_tampered_old_provenance_or_body_aborts_before_any_artifact_write(self):
        for field in ['provenance', 'body']:
            with self.subTest(field=field):
                root = self.fixture()
                history = json.loads((root / HISTORY).read_bytes())
                if field == 'provenance':
                    history['receipts'][0]['provenance']['dateMeaning'] += ' forged'
                else:
                    history['results'][0]['result']['transformed'][0]['text'] += 'X'
                (root / HISTORY).write_text(stable(history), encoding='utf-8')
                before = {name: (root / name).read_bytes() for name in [HISTORY, JAVASCRIPT]}
                with self.assertRaises(subprocess.CalledProcessError):
                    build(root)
                self.assertEqual({name: (root / name).read_bytes() for name in before}, before)

    def test_duplicate_conflicting_receipt_is_rejected_not_last_write_wins(self):
        history = json.loads((ROOT / HISTORY).read_bytes())
        duplicate = copy.deepcopy(history['receipts'][0])
        duplicate['createdAt'] = '2000-01-01T00:00:00.000Z'
        history['receipts'].append(duplicate)
        with self.assertRaises(subprocess.CalledProcessError):
            merge(history, [])

    def test_explicit_local_public_ancestry_seed_is_persisted_then_git_can_be_removed(self):
        root = self.fixture()
        history = json.loads((root / HISTORY).read_bytes())
        current_count = json.loads((root / CURRENT[0]).read_bytes())
        old = next(r for r in history['receipts'] if r['registrySchema'] == current_count['schema'] and r['revision'] != current_count['entries'][0]['revision'])
        task = next(t['task'] for t in history['tasks'] if t['id'] == old['taskId'])
        result = next(r['result'] for r in history['results'] if r['id'] == old['resultId'])
        manifest = {'schema': old['registrySchema'], 'records': [{'recordId': old['recordId'], 'revision': old['revision'], 'provenance': old['provenance']}], 'entries': [{'recordId': old['recordId'], 'revision': old['revision'], 'caseId': old['caseId'], 'task': task, 'inputVersion': old['inputVersion'], 'run': {'id': old['resultId'], 'createdAt': old['createdAt'], 'result': result}}]}
        (root / HISTORY).unlink()
        (root / JAVASCRIPT).unlink()
        (root / CURRENT[0]).write_text(stable(manifest), encoding='utf-8')
        git = lambda *args: subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
        git('init', '-q')
        git('add', CURRENT[0])
        git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Published fixture history')
        git('update-ref', 'refs/remotes/origin/main', 'HEAD')
        (root / CURRENT[0]).write_text(stable(current_count), encoding='utf-8')
        retained = build(root, seed_public_git=True)
        self.assertTrue(any(r['revision'] == old['revision'] for r in retained['receipts']))
        self.assertEqual(len(retained['seedSources']), 1)
        metadata, retired = root / '.git', root / 'retired-git-metadata'
        self.assertEqual(metadata.resolve().parent, root.resolve())
        self.assertEqual(retired.resolve().parent, root.resolve())
        metadata.rename(retired)
        self.assertFalse((root / '.git').exists())
        self.assertEqual(build(root, write=False), retained)


if __name__ == '__main__':
    unittest.main()
