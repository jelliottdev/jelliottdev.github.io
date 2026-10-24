"""Git-backed integration tests for opt-in bundle selection."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from test_experiment_bundles import select_records


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


class BundleSelectionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='bundle-selection-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        git(self.root, 'init', '-q')
        git(self.root, 'config', 'user.email', 'test@example.invalid')
        git(self.root, 'config', 'user.name', 'Bundle test')
        self.records = [self.record('alpha', 'data/pages/page.json', 'inputs/absent.txt'),
                        self.record('beta', 'data/pages/page.json')]
        self.write('data/experiments.json', json.dumps({'records': self.records}))
        self.write('data/pages/page.json', '{}')
        self.write('scripts/verify_bundle.py', 'original helper\n')
        self.write('experiments/records/alpha/article.md', 'old article\n')
        self.write('experiments/records/beta/article.md', 'old article\n')
        self.write('downloads/experiments/alpha.zip', 'alpha archive\n')
        self.write('downloads/experiments/beta.zip', 'beta archive\n')
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'baseline')

    def record(self, identifier, *inputs):
        return {'id': identifier,
                'reproduction': {'inputs': [{'path': p} for p in inputs], 'outputs': []},
                'scope': {'artifacts': []}}

    def write(self, path, value):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(value, encoding='utf-8')

    def selected(self):
        return select_records(self.root, self.records, 'HEAD')

    def test_new_record_from_registry_and_untracked_archive(self):
        self.records.append(self.record('gamma'))
        self.write('data/experiments.json', json.dumps({'records': self.records}))
        self.write('downloads/experiments/gamma.zip', 'new archive\n')
        ids, reason = self.selected()
        self.assertEqual(ids, {'gamma'})
        self.assertIn('changed since', reason)

    def test_shared_declared_dependency_selects_affected_records(self):
        self.write('data/pages/page.json', '{"updated":true}')
        ids, _ = self.selected()
        self.assertEqual(ids, {'alpha', 'beta'})

    def test_untracked_declared_input_selects_its_record(self):
        self.write('inputs/absent.txt', 'new untracked input\n')
        ids, _ = self.selected()
        self.assertEqual(ids, {'alpha'})

    def test_staged_record_article_does_not_select_all(self):
        self.write('experiments/records/beta/article.md', 'new article\n')
        git(self.root, 'add', 'experiments/records/beta/article.md')
        ids, _ = self.selected()
        self.assertEqual(ids, {'beta'})

    def test_experiment_zip_selects_its_record(self):
        self.write('downloads/experiments/alpha.zip', 'new archive\n')
        ids, _ = self.selected()
        self.assertEqual(ids, {'alpha'})

    def test_record_artifact_selects_owner_and_cross_record_consumer(self):
        self.records.append(self.record('gamma', 'experiments/records/alpha/inputs.json'))
        self.write('data/experiments.json', json.dumps({'records': self.records}))
        self.write('experiments/records/alpha/inputs.json', 'original\n')
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'declare cross-record input')
        self.write('experiments/records/alpha/inputs.json', 'changed\n')
        ids, _ = self.selected()
        self.assertEqual(ids, {'alpha', 'gamma'})

    def test_record_script_selects_cross_record_consumer(self):
        self.records.append(self.record('gamma'))
        self.records[-1]['reproduction']['script'] = 'experiments/records/alpha/run.py'
        self.write('data/experiments.json', json.dumps({'records': self.records}))
        self.write('experiments/records/alpha/run.py', 'original\n')
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'declare cross-record script')
        self.write('experiments/records/alpha/run.py', 'changed\n')
        ids, _ = self.selected()
        self.assertEqual(ids, {'alpha', 'gamma'})

    def test_registry_finding_change_selects_its_record(self):
        changed = copy.deepcopy(self.records)
        changed[1]['finding'] = 'changed finding'
        self.records = changed
        self.write('data/experiments.json', json.dumps({'records': self.records}))
        ids, _ = self.selected()
        self.assertEqual(ids, {'beta'})

    def test_release_generated_outputs_do_not_expand_selection(self):
        self.records.append(self.record('gamma'))
        self.write('data/experiments.json', json.dumps({'records': self.records}))
        self.write('downloads/experiments/gamma.zip', 'new archive\n')
        for path in ('data/catalog.json', 'data/experiment-index.json', 'data/checker-records.json',
                     'data/articles.json', 'data/article-search.json',
                     'data/guide-index.json', 'data/method-families.json', 'data/research-map.json',
                     'downloads/SHA256SUMS.txt', 'downloads/reference-data.zip'):
            self.write(path, 'generated\n')
        ids, reason = self.selected()
        self.assertEqual(ids, {'gamma'})
        self.assertIn('changed since', reason)

    def test_generated_name_declared_as_input_still_selects_record(self):
        self.records[0]['reproduction']['inputs'].append({'path': 'data/catalog.json'})
        self.write('data/experiments.json', json.dumps({'records': self.records}))
        git(self.root, 'add', 'data/experiments.json')
        git(self.root, 'commit', '-qm', 'declare dependency')
        self.write('data/catalog.json', 'changed generated dependency\n')
        ids, _ = self.selected()
        self.assertEqual(ids, {'alpha'})

    def test_helper_change_forces_full_validation(self):
        self.write('scripts/verify_bundle.py', 'modified shared helper\n')
        ids, reason = self.selected()
        self.assertEqual(ids, {'alpha', 'beta'})
        self.assertIn('full fallback', reason)

    def test_browser_retrieval_check_alone_does_not_reextract_bundles(self):
        self.write('scripts/test_assistant.cjs', 'browser retrieval check\n')
        self.assertEqual(self.selected()[0], set())

    def test_reviewed_exceptions_still_select_declared_consumers(self):
        for name in ('scripts/test_assistant.cjs', 'data/research-map.json'):
            self.records[0]['reproduction']['inputs'].append({'path': name})
            self.write(name, 'original\n')
        self.write('data/experiments.json', json.dumps({'records': self.records}))
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'declare reviewed paths as dependencies')
        self.write('scripts/test_assistant.cjs', 'changed test dependency\n')
        self.write('data/research-map.json', 'changed map dependency\n')
        self.assertEqual(self.selected()[0], {'alpha'})

    def test_unknown_check_or_data_still_forces_all(self):
        for name in ('scripts/test_unknown.cjs', 'data/unknown.json'):
            self.write(name, 'unknown\n')
            ids, reason = self.selected()
            self.assertEqual(ids, {'alpha', 'beta'})
            self.assertIn('full fallback', reason)
            (self.root / name).unlink()

    def test_dependency_in_baseline_still_selects_after_declaration_removed(self):
        self.records[0]['reproduction']['inputs'].append({'path': 'data/research-map.json'})
        self.write('data/research-map.json', 'original\n')
        self.write('data/experiments.json', json.dumps({'records': self.records}))
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'baseline map dependency')
        self.records[0]['reproduction']['inputs'].pop()
        self.write('data/research-map.json', 'changed\n')
        self.assertEqual(self.selected()[0], {'alpha'})

    def test_missing_baseline_forces_full_validation(self):
        ids, reason = select_records(self.root, self.records, 'missing-ref')
        self.assertEqual(ids, {'alpha', 'beta'})
        self.assertIn('full fallback', reason)

    def test_generated_child_of_declared_directory_selects_consumer(self):
        self.records[0]['scope']['artifacts'].append('data')
        self.write('data/experiments.json', json.dumps({'records': self.records}))
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'declare directory')
        self.write('data/research-map.json', 'changed generated child\n')
        self.assertEqual(self.selected()[0], {'alpha'})

    def test_path_aliases_cannot_hide_declared_consumers(self):
        self.records[0]['reproduction']['inputs'].append({'path': './data/research-map.json'})
        self.records[1]['reproduction']['inputs'].append({'path': 'scripts\\test_assistant.cjs'})
        self.write('data/experiments.json', json.dumps({'records': self.records}))
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'declare path aliases')
        self.write('data/research-map.json', 'changed\n')
        self.write('scripts/test_assistant.cjs', 'changed\n')
        self.assertEqual(self.selected()[0], {'alpha', 'beta'})

    def test_registry_change_also_selects_declared_directory_consumer(self):
        self.records[0]['scope']['artifacts'].append('data')
        self.write('data/experiments.json', json.dumps({'records': self.records}))
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'declare registry directory consumer')
        self.records[1]['finding'] = 'updated finding'
        self.write('data/experiments.json', json.dumps({'records': self.records}))
        self.assertEqual(self.selected()[0], {'alpha', 'beta'})


if __name__ == '__main__':
    unittest.main()
