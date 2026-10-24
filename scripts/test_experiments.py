"""Registry regression tests; fixtures never enter the published repository."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from build_experiments import build, CHECKER_FIELDS
from preflight_experiments import preflight
from build_experiment_bundles import build as build_bundle


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
        checker_bytes = (self.root / 'data/checker-records.json').read_bytes()
        checker = json.loads(checker_bytes)
        self.assertEqual(checker['schema'], 'liberpedia-checker-records-v1')
        self.assertEqual(checker['registry_sha256'], hashlib.sha256(
            (self.root / 'data/experiments.json').read_bytes()).hexdigest())
        self.assertEqual(checker['records'], [{key: record[key] for key in CHECKER_FIELDS
                                              if key in record} for record in records])
        self.assertEqual(checker['records'][0]['scope'], records[0]['scope'])
        self.assertEqual(checker['records'][0]['article'], records[0]['article'])
        self.assertNotIn('reproduction', checker['records'][0])
        self.assertNotIn('sources', checker['records'][0])
        self.run_build()
        self.assertEqual((self.root / 'data/checker-records.json').read_bytes(), checker_bytes)
        self.record['status'] = 'draft'
        self.assertEqual(self.run_build(), [])
        self.assertFalse(exported.exists(), 'A withdrawn record must not survive in generated individual exports')
        self.assertEqual(json.loads((self.root / 'data/experiment-index.json').read_text())['records'], [])
        self.assertEqual(json.loads((self.root / 'data/checker-records.json').read_text())['records'], [])
        self.assertNotIn('Fixture', (self.root / 'reference/experiments.html').read_text(encoding='utf-8'))

    def test_materials_preserves_reviewed_reuse_limits_and_rejects_unbound_notes(self):
        materials = {'summary': 'Scores and hashes only.', 'reuse': 'Inspect retained scores.',
                     'limits': 'Decoded text requires reconstruction.',
                     'evidence': ['experiments/records/test-record/output.txt']}
        record = copy.deepcopy(self.record)
        record['materials'] = materials
        self.assertEqual(self.run_build(record)[0]['materials'], materials)
        checker = json.loads((self.root / 'data/checker-records.json').read_text())
        self.assertEqual(checker['records'][0]['materials'], materials)
        for changed in [None, {**materials, 'reuse': ''}, {**materials, 'verified': True},
                        {**materials, 'summary': 'x' * 1201},
                        {**materials, 'evidence': ['missing.json']},
                        {**materials, 'evidence': materials['evidence'] * 2}]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                self.run_build({**record, 'materials': changed})

    def test_discovery_is_optional_strict_and_preserved_in_checker(self):
        operation = {'action': 'reverse', 'operand': 'rune-order', 'within': 'row'}
        hint = {'operations': [operation], 'evaluation': ['known-opening']}
        self.assertNotIn('discovery', self.run_build()[0])
        record = {**self.record, 'discovery': hint}
        self.assertEqual(self.run_build(record)[0]['discovery'], hint)
        checker = json.loads((self.root / 'data/checker-records.json').read_text())
        self.assertEqual(checker['records'][0]['discovery'], hint)
        for operand in ('rune-order', 'word-order'):
            for within in ('row', 'word', 'page'):
                valid = {'operations': [{**operation, 'operand': operand, 'within': within}],
                         'evaluation': ['known-opening', 'english-readability']}
                self.assertEqual(self.run_build({**record, 'discovery': valid})[0]['discovery'], valid)
        invalid = [None, {}, {**hint, 'coverage': True},
                   {**hint, 'operations': []}, {**hint, 'operations': [operation] * 2},
                   {**hint, 'operations': [operation] * 9},
                   {**hint, 'operations': [{**operation, 'action': 'rotate'}]},
                   {**hint, 'operations': [{**operation, 'operand': 'letters'}]},
                   {**hint, 'operations': [{**operation, 'within': 'column'}]},
                   {**hint, 'operations': [{**operation, 'extra': True}]},
                   {**hint, 'operations': ['reverse']},
                   {**hint, 'evaluation': []}, {**hint, 'evaluation': ['known-opening'] * 2},
                   {**hint, 'evaluation': ['english']}, {**hint, 'evaluation': 'known-opening'},
                   {**hint, 'evaluation': [None]}, {**hint, 'evaluation': [[]]}]
        for changed in invalid:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                self.run_build({**record, 'discovery': changed})

    def test_article_link_permissions_are_derived_not_imported(self):
        record = copy.deepcopy(self.record)
        record['article_links'] = {'invented.json': 'research/unreviewed.json'}
        self.assertNotIn('article_links', self.run_build(record)[0])

    def test_generated_python_cache_is_not_a_reproduction_input(self):
        record = copy.deepcopy(self.record)
        path = 'experiments/records/test-record/__pycache__/run.cpython-312.pyc'
        target = self.root / path
        target.parent.mkdir()
        target.write_bytes(b'generated cache')
        record['reproduction']['inputs'].append({
            'path': path, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
        with self.assertRaisesRegex(ValueError, 'generated Python caches'):
            self.run_build(record)

    def test_bundle_rejects_a_changed_reviewed_dependency(self):
        record = self.run_build()[0]
        verifier = self.root / 'scripts/verify_bundle.py'
        verifier.parent.mkdir()
        verifier.write_text('# fixture verifier', encoding='utf-8')
        (self.root / record['reproduction']['inputs'][0]['path']).write_bytes(b'changed after validation')
        with self.assertRaisesRegex(ValueError, 'differs from reviewed hash'):
            build_bundle(self.root, record)

    def test_draft_preflight_preserves_status_and_every_site_file(self):
        self.run_build()
        self.record['status'] = 'draft'
        path = self.root / 'experiments/records/test-record/record.json'
        path.write_text(json.dumps(self.record))
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = preflight(['test-record'], self.root)
        self.assertEqual(result[0]['status'], 'draft')
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_draft_preflight_rejects_stale_result_hash(self):
        self.run_build()
        self.record['status'] = 'draft'
        (self.root / 'experiments/records/test-record/record.json').write_text(json.dumps(self.record))
        (self.root / self.record['reproduction']['outputs'][0]['path']).write_text('changed')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            preflight(['test-record'], self.root)

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

    def test_reproduction_command_checker_must_be_bundled(self):
        relative = 'experiments/records/test-record/check.py'
        helper = self.root / relative
        helper.write_text('print("independent check")\n', encoding='utf-8')
        self.record['reproduction']['command'] += ' && python ' + relative
        with self.assertRaisesRegex(ValueError, 'undeclared bundle files.*check.py'):
            self.run_build()
        self.record['reproduction']['inputs'].append({
            'path': relative, 'sha256': hashlib.sha256(helper.read_bytes()).hexdigest()})
        self.assertEqual(len(self.run_build()), 1)

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
        variant['reproduction']['command'] = 'python ' + prefix + 'run.py'
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
