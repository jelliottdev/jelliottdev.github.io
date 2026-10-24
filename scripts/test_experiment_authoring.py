"""Authoring policy and actual committed Git transition regression tests."""
import importlib.util
import json
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


if __name__ == '__main__':
    unittest.main()
