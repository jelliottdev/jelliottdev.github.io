"""Frozen scientific checks survive presentation edits without caller writes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('archived_program_projection', ROOT / 'scripts/published_program_projection.py')
projection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(projection)


class ArchivedRecipePresentationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='archived-presentation-test-')
        self.root = Path(self.temporary.name)
        for name in projection.source_files(ROOT):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        self.plan = json.loads((self.root / projection.BASE / 'plan.json').read_bytes())

    def tearDown(self):
        self.temporary.cleanup()

    def files(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()}

    def check(self):
        before = self.files()
        commands = []
        original_run = subprocess.run

        def run(command, **options):
            commands.append(command)
            self.assertEqual(command[0], sys.executable)
            self.assertNotEqual(Path(options['cwd']), self.root)
            self.assertIn(Path(command[1]).name, ('run.py', 'check.py'))
            return original_run(command, **options)

        with mock.patch.object(projection, 'build', side_effect=AssertionError('No target projection build')):
            with mock.patch.object(projection.subprocess, 'run', side_effect=run):
                output = projection.reproduce_archive(self.root)
        self.assertEqual([Path(c[1]).name for c in commands], ['run.py', 'check.py'])
        self.assertEqual(commands[0][2:], ['--check'])
        self.assertEqual(commands[1][2:], [])
        self.assertIn('zero new target decodes', output[0])
        self.assertIn('no full target transformation', output[1])
        self.assertEqual(self.files(), before)

    def test_current_presentation_runs_both_frozen_checks_without_caller_writes(self):
        self.check()

    def test_titles_and_motivations_can_change_without_editing_scientific_identity(self):
        paths = {item['path'] for item in self.plan['recipe_identities']}
        for name in paths:
            path = self.root / name
            record = json.loads(path.read_bytes())
            for recipe in record['browser_followups']:
                recipe['title'] = 'A clearer description of the same declared calculation'
                recipe['motivation'] = 'Explain the existing calculation without changing its settings.'
            path.write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
        self.check()

    def test_mathematical_recipe_mutation_fails_before_archived_scripts(self):
        identity = self.plan['recipe_identities'][0]
        path = self.root / identity['path']
        record = json.loads(path.read_bytes())
        recipe = next(item for item in record['browser_followups'] if item['id'] == identity['id'])
        recipe['card']['rules']['evaluation']['value']['values'][0] = 0
        path.write_text(json.dumps(record), encoding='utf-8')
        before = self.files()
        with mock.patch.object(projection.subprocess, 'run', side_effect=AssertionError('No script before identity validation')):
            with self.assertRaisesRegex(ValueError, 'mathematical definition'):
                projection.reproduce_archive(self.root)
        self.assertEqual(self.files(), before)

    def test_every_frozen_scientific_source_and_input_remains_pinned(self):
        for name in projection.DECLARATION['sourceSha256']:
            with self.subTest(source=name):
                path = self.root / name
                saved = path.read_bytes()
                path.write_bytes(saved + b'\n')
                before = self.files()
                with mock.patch.object(projection.subprocess, 'run', side_effect=AssertionError('No script before source validation')):
                    with self.assertRaisesRegex(ValueError, 'scientific source pin changed'):
                        projection.reproduce_archive(self.root)
                self.assertEqual(self.files(), before)
                path.write_bytes(saved)
        item = self.plan['inputs'][0]
        path = self.root / item['path']
        path.write_bytes(path.read_bytes() + b'\n')
        with mock.patch.object(projection.subprocess, 'run', side_effect=AssertionError('No script before input validation')):
            with self.assertRaisesRegex(ValueError, 'input pin changed'):
                projection.reproduce_archive(self.root)

    def test_record_documents_wrapper_and_exact_current_presentation_dependencies(self):
        record = json.loads((ROOT / projection.BASE / 'record.json').read_bytes())
        self.assertEqual(record['reproduction']['command'],
                         'python scripts/published_program_projection.py --reproduce-archive')
        self.assertIn(record['reproduction']['command'], record['analysis'])
        workflow = (ROOT / '.github/workflows/validate-experiments.yml').read_text(encoding='utf-8')
        self.assertIn('run: ' + record['reproduction']['command'], workflow)
        self.assertIn('run: python scripts/test_archived_recipe_presentation.py', workflow)
        self.assertNotIn('run: python experiments/records/prepared-opening-evidence-gates/run.py', workflow)
        self.assertNotIn('run: python experiments/records/prepared-opening-evidence-gates/check.py', workflow)
        self.assertNotIn('python experiments/records/prepared-opening-evidence-gates/run.py --check', record['analysis'])
        inputs = {item['path']: item['sha256'] for item in record['reproduction']['inputs']}
        for name in ['scripts/published_program_projection.py',
                     'experiments/records/cumulative-autokey-literal/record.json',
                     'experiments/records/lp2-row-column-routes/record.json']:
            self.assertEqual(inputs[name], hashlib.sha256((ROOT / name).read_bytes()).hexdigest())
        for name, digest in projection.DECLARATION['sourceSha256'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()
