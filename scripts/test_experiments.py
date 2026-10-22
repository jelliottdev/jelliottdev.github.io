"""Registry regression tests; fixtures never enter the published repository."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from build_experiments import build


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='liberpedia-test-')
        self.root = Path(self.temp.name)
        for folder in ('data', 'reference', 'experiments/records/test-record'):
            (self.root / folder).mkdir(parents=True)
        (self.root / 'data/index.json').write_text('{"pages":[{"id":"lp2-15"}]}')
        prefix = 'experiments/records/test-record/'
        for name, content in [('run.py', 'print(1)\n'), ('input.txt', 'input'), ('output.txt', '1')]:
            (self.root / prefix / name).write_text(content, encoding='utf-8')
        (self.root / prefix / 'article.md').write_text('A fixture account of a bounded test. ' * 10)
        def file(name):
            path = prefix + name
            return {'path': path, 'sha256': hashlib.sha256((self.root / path).read_bytes()).hexdigest()}
        self.record = {
            'id': 'test-record', 'title': 'Fixture', 'status': 'published', 'question': 'Question?',
            'summary': 'A fixture only', 'tags': ['prime'],
            'scope': {'pages': ['lp2-15'], 'representation': 'raw runes', 'procedure': 'sum',
                      'parameters': 'one row', 'exclusions': 'other rows'},
            'outcome': 'inconclusive', 'finding': 'A limited result', 'limitations': 'Limited scope',
            'next_steps': 'Review another row', 'review': {'reviewer': 'Test fixture', 'retested_on': '2026-01-01',
                                                          'kind': 'computational', 'human_review': 'pending'},
            'reproduction': {'command': 'python '+prefix+'run.py', 'environment': 'Python 3',
                             'script': prefix+'run.py', 'script_sha256': file('run.py')['sha256'], 'inputs': [file('input.txt')], 'outputs': [file('output.txt')]},
            'sources': [{'label': 'Fixture', 'url': 'https://example.com/source'}], 'related': []
        }

    def tearDown(self):
        self.temp.cleanup()

    def run_build(self, record=None):
        (self.root / 'experiments/records/test-record/record.json').write_text(json.dumps(record or self.record))
        return build(self.root)

    def test_published_record_and_draft_exclusion(self):
        records = self.run_build()
        self.assertEqual(len(records), 1)
        exported = self.root / 'reference/experiments/test-record.json'
        self.assertEqual(json.loads(exported.read_text(encoding='utf-8')), records[0])
        discovery = json.loads((self.root / 'data/experiment-index.json').read_text(encoding='utf-8'))
        self.assertEqual([item['id'] for item in discovery['records']], ['test-record'])
        self.assertTrue(discovery['records'][0]['record_url'].endswith('/reference/experiments/test-record.json'))
        self.assertNotIn('article', discovery['records'][0])
        self.assertNotIn('reproduction', discovery['records'][0])
        self.record['status'] = 'draft'
        self.assertEqual(self.run_build(), [])
        self.assertFalse(exported.exists(), 'A withdrawn record must not survive in generated individual exports')
        self.assertEqual(json.loads((self.root / 'data/experiment-index.json').read_text())['records'], [])
        self.assertNotIn('Fixture', (self.root / 'reference/experiments.html').read_text(encoding='utf-8'))

    def test_changed_script_or_missing_reviewed_hash_rejected(self):
        reviewed_hash = self.record['reproduction'].pop('script_sha256')
        with self.assertRaisesRegex(ValueError, 'Script SHA-256 mismatch'):
            self.run_build()
        self.record['reproduction']['script_sha256'] = reviewed_hash
        script = self.root / self.record['reproduction']['script']
        script.write_text('print(2)\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Script SHA-256 mismatch'):
            self.run_build()
        self.record['reproduction']['script_sha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
        result = self.run_build()
        self.assertEqual(result[0]['script_sha256'], self.record['reproduction']['script_sha256'])

    def test_changed_result_rejected(self):
        (self.root / self.record['reproduction']['outputs'][0]['path']).write_text('changed')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            self.run_build()

    def add_plan_fixture(self, input_digest=None, report_digest=None, declare_dependency=True):
        prefix = 'experiments/records/test-record/'
        original = self.record['reproduction']['inputs'][0]
        plan = {'inputs': [{'path': original['path'],
                            'sha256': input_digest or original['sha256']}]}
        plan_path = self.root / prefix / 'plan.json'
        plan_path.write_text(json.dumps(plan), encoding='utf-8')
        plan_digest = hashlib.sha256(plan_path.read_bytes()).hexdigest()
        results_path = self.root / prefix / 'results.json'
        results_path.write_text(json.dumps({'plan_sha256': report_digest or plan_digest,
                                           'measurement': 42}), encoding='utf-8')
        self.record['reproduction']['inputs'] = ([original] if declare_dependency else []) + [
            {'path': prefix+'plan.json', 'sha256': plan_digest}]
        self.record['reproduction']['outputs'] = [
            {'path': prefix+'results.json',
             'sha256': hashlib.sha256(results_path.read_bytes()).hexdigest()}]

    def test_matching_plan_and_report_provenance(self):
        self.add_plan_fixture()
        self.assertEqual(len(self.run_build()), 1)

    def test_stale_plan_dependency_despite_current_record_hashes(self):
        self.add_plan_fixture(input_digest='0'*64)
        with self.assertRaisesRegex(ValueError, 'Plan input SHA-256 mismatch'):
            self.run_build()
        self.assertFalse((self.root / 'data/experiments.json').exists())

    def test_stale_report_plan_despite_current_record_hashes(self):
        self.add_plan_fixture(report_digest='0'*64)
        with self.assertRaisesRegex(ValueError, 'Saved report plan SHA-256 mismatch'):
            self.run_build()
        self.assertFalse((self.root / 'data/experiments.json').exists())

    def test_plan_dependency_missing_from_bundle_declaration(self):
        self.add_plan_fixture(declare_dependency=False)
        with self.assertRaisesRegex(ValueError, 'Plan dependency must be a declared input'):
            self.run_build()

    def test_invalid_scope_and_missing_review_rejected(self):
        for change in ('scope', 'review', 'related'):
            record = copy.deepcopy(self.record)
            if change == 'scope': record['scope']['pages'] = ['lp2-99']
            if change == 'review': record['review']['reviewer'] = ''
            if change == 'related': record['related'] = ['missing']
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.run_build(record)

    def test_human_review_requires_named_dated_findings(self):
        for field in ('kind', 'human_review'):
            record = copy.deepcopy(self.record)
            record['review'].pop(field)
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.run_build(record)
        record = copy.deepcopy(self.record)
        record['review']['human_review'] = 'complete'
        for field in ('human_reviewer', 'human_reviewed_on', 'human_findings'):
            with self.subTest(missing=field), self.assertRaises(ValueError):
                self.run_build(record)
            record['review'][field] = ('2026-01-02' if field == 'human_reviewed_on'
                                       else 'Independent reviewer' if field == 'human_reviewer'
                                       else 'Compared the declared source and output.')
        self.assertEqual(len(self.run_build(record)), 1)

    def test_family_baseline_and_variant_differences(self):
        self.record['family'] = {'id': 'test-family', 'title': 'Pair counts',
                                 'question': 'Does ordering matter?', 'baseline': 'test-record'}
        self.record['variant'] = {'label': 'Baseline', 'changes': []}
        self.run_build()
        variant = copy.deepcopy(self.record)
        variant['id'] = 'test-variant'
        prefix = 'experiments/records/test-variant/'
        folder = self.root / prefix
        folder.mkdir()
        for name in ('run.py', 'article.md'):
            (folder / name).write_bytes((self.root / 'experiments/records/test-record' / name).read_bytes())
        variant['reproduction']['script'] = prefix + 'run.py'
        variant['scope']['parameters'] = 'two rows'
        variant['variant'] = {'label': 'Two-row variant', 'changes': [
            {'field': 'parameters', 'before': 'one row', 'after': 'two rows',
             'reason': 'Check sensitivity to the selected region.'}]}
        path = folder / 'record.json'
        path.write_text(json.dumps(variant))
        self.assertEqual(len(self.run_build()), 2)
        for mutation in ('missing', 'wrong', 'baseline'):
            bad = copy.deepcopy(variant)
            if mutation == 'missing': bad['variant']['changes'] = []
            if mutation == 'wrong': bad['variant']['changes'][0]['before'] = 'invented'
            if mutation == 'baseline': bad['family']['baseline'] = 'missing'
            path.write_text(json.dumps(bad))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.run_build()

    def test_artifact_scope_requires_hashed_inputs(self):
        self.record['scope']['pages'] = []
        with self.assertRaisesRegex(ValueError, 'pages or source artifacts'):
            self.run_build()
        self.record['scope']['artifacts'] = [self.record['reproduction']['inputs'][0]['path']]
        self.assertEqual(len(self.run_build()), 1)
        self.record['scope']['artifacts'] = ['undeclared.pdf']
        with self.assertRaisesRegex(ValueError, 'declared hashed inputs'):
            self.run_build()

    def test_path_escape_rejected(self):
        self.record['reproduction']['inputs'][0]['path'] = '../outside.txt'
        with self.assertRaisesRegex(ValueError, 'escapes repository'):
            self.run_build()


if __name__ == '__main__':
    unittest.main()
