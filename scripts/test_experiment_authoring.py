"""Authoring policy and actual committed Git transition regression tests."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('authoring', ROOT / 'scripts/check_experiment_authoring.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AuthoringTests(unittest.TestCase):
    def test_event_baselines(self):
        sha = 'a' * 40
        self.assertEqual(module.event_base('push', {'before': sha}), sha)
        self.assertEqual(module.event_base('pull_request', {'pull_request': {'base': {'sha': sha}}}), sha)
        self.assertEqual(module.event_base('push', {'before': '0' * 40}), 'HEAD^')
        self.assertEqual(module.event_base('workflow_dispatch', {}), 'HEAD^')
        for name, event in [('push', {}), ('push', {'before': '--help'}), ('push', {'before': 'a' * 39}),
                            ('pull_request', {}), ('pull_request', {'pull_request': None}),
                            ('pull_request', {'pull_request': {'base': []}}),
                            ('pull_request', {'pull_request': {'base': {'sha': '0' * 40}}})]:
            with self.subTest(name=name, event=event), self.assertRaises(ValueError):
                module.event_base(name, event)

    def test_policy(self):
        v2 = {'schema': module.SCHEMA, 'status': 'draft'}
        for status in ('draft', 'published'):
            self.assertTrue(module.validate_transition(None, {'status': status}))
            self.assertFalse(module.validate_transition(None, dict(v2, status=status)))
        self.assertTrue(module.validate_transition({'status': 'draft'}, {'status': 'published'}))
        self.assertFalse(module.validate_transition({'status': 'published'}, {'status': 'published', 'finding': 'Updated legacy result'}))
        self.assertFalse(module.validate_transition({'status': 'draft'}, {'status': 'draft'}))
        for status in ('draft', 'published'):
            self.assertTrue(module.validate_transition(v2, {'status': status}))
        self.assertFalse(module.validate_transition({'status': 'draft'}, dict(v2, status='published')))
        self.assertTrue(module.validate_transition(None, []))

    def test_real_git_cli(self):
        with tempfile.TemporaryDirectory(prefix='authoring-git-') as folder:
            root = Path(folder)
            (root / 'scripts').mkdir()
            script = root / 'scripts/check_experiment_authoring.py'
            shutil.copyfile(ROOT / 'scripts/check_experiment_authoring.py', script)
            def git(*args):
                return subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True).stdout.decode().strip()
            def write(name, value):
                path = root / 'experiments/records' / name / 'record.json'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value), encoding='utf-8')
            def commit():
                git('add', '.'); git('commit', '-qm', 'fixture')
                return git('rev-parse', 'HEAD')
            def run(*args):
                return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)
            git('init', '-q');git('config', 'user.name', 'Test');git('config', 'user.email', 'test@example.invalid')
            write('legacy', {'status': 'published'})
            write('draft', {'status': 'draft'})
            write('modern', {'schema': module.SCHEMA, 'status': 'published'})
            write('deleted', {'status': 'published'})
            baseline = commit()
            self.assertNotEqual(run().returncode, 0)
            self.assertIn('--base', run().stderr)
            write('legacy', {'status': 'published', 'finding': 'Edited'})
            write('draft', {'status': 'published'})
            write('modern', {'status': 'published'})
            write('added', {'status': 'draft'})
            (root / 'experiments/records/deleted/record.json').unlink()
            commit()
            rejected = run()
            self.assertNotEqual(rejected.returncode, 0)
            for name in ('draft', 'modern', 'added'):
                self.assertIn('records/' + name + '/record.json', rejected.stderr)
            self.assertNotIn('records/legacy/', rejected.stderr)
            self.assertNotIn('records/deleted/', rejected.stderr)
            # A later unrelated commit must not conceal an earlier invalid record.
            (root / 'wording.txt').write_text('Unrelated follow-up', encoding='utf-8')
            commit()
            self.assertEqual(run().returncode, 0)  # The old last-commit check misses it.
            event_file = root / 'event.json'
            for name, event in [('push', {'before': baseline}),
                                ('pull_request', {'pull_request': {'base': {'sha': baseline}}})]:
                event_file.write_text(json.dumps(event), encoding='utf-8')
                env = dict(os.environ, GITHUB_EVENT_NAME=name, GITHUB_EVENT_PATH=str(event_file))
                batch = subprocess.run([sys.executable, str(script), '--github-event'], env=env, capture_output=True, text=True)
                self.assertNotEqual(batch.returncode, 0, batch.stdout)
                self.assertIn('records/added/record.json', batch.stderr)
            event_file.unlink()
            for name in ('draft', 'modern', 'added'):
                write(name, {'schema': module.SCHEMA, 'status': 'published' if name != 'added' else 'draft'})
            commit()
            accepted = run('--base', baseline)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertIn('3 committed records checked', accepted.stdout)
            # Uncommitted invalid data must not change a committed HEAD check.
            write('added', {'status': 'draft'})
            self.assertEqual(run('--base', baseline).returncode, 0)
            self.assertNotEqual(run('--base', 'missing-ref').returncode, 0)
            self.assertNotEqual(run('--base', '--help').returncode, 0)

    def test_shallow_baseline_fetch(self):
        with tempfile.TemporaryDirectory(prefix='authoring-fetch-') as folder:
            root = Path(folder)
            source, checkout = root / 'source', root / 'checkout'
            source.mkdir()
            def git(where, *args):
                return subprocess.run(['git', '-C', str(where), *args], capture_output=True, check=True).stdout.decode().strip()
            git(source, 'init', '-q')
            git(source, 'config', 'user.name', 'Test')
            git(source, 'config', 'user.email', 'test@example.invalid')
            (source / 'baseline.txt').write_text('baseline', encoding='utf-8')
            git(source, 'add', '.'); git(source, 'commit', '-qm', 'baseline')
            baseline = git(source, 'rev-parse', 'HEAD')
            path = source / 'experiments/records/new/record.json'
            path.parent.mkdir(parents=True)
            path.write_text('{"status":"draft"}', encoding='utf-8')
            git(source, 'add', '.'); git(source, 'commit', '-qm', 'invalid legacy addition')
            (source / 'wording.txt').write_text('follow-up', encoding='utf-8')
            git(source, 'add', '.'); git(source, 'commit', '-qm', 'unrelated')
            subprocess.run(['git', 'clone', '-q', '--depth=1', source.as_uri(), str(checkout)], check=True, capture_output=True)
            with self.assertRaises(ValueError):
                module.check(checkout, baseline)
            module.fetch_baseline(checkout, baseline)
            count, errors = module.check(checkout, baseline)
            self.assertEqual(count, 1)
            self.assertTrue(any('New records' in error for error in errors))
            # Once present, an unavailable origin must not trigger a needless fetch.
            git(checkout, 'remote', 'set-url', 'origin', str(root / 'missing-origin'))
            module.fetch_baseline(checkout, baseline)


if __name__ == '__main__':
    unittest.main()
