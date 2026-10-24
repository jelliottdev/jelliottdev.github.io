"""CI dispatch retains full checks whenever a safe comparison cannot be named."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import ci_experiment_bundles as dispatch


class DispatchTests(unittest.TestCase):
    def test_push_and_pull_request_pass_a_literal_sha_argument(self):
        for sha in ('a' * 40, 'b' * 64):
            for name, event in [('push', {'before': sha}),
                                ('pull_request', {'pull_request': {'base': {'sha': sha}}})]:
                self.assertEqual(dispatch.command(name, event)[-2:], ['--changed-from', sha])

    def test_manual_unknown_missing_and_unsafe_baselines_are_full(self):
        full = dispatch.command('workflow_dispatch', {})
        for name in ('workflow_dispatch', 'schedule', 'unknown', None):
            self.assertEqual(dispatch.command(name, {'before': 'a' * 40}), full)
        for event in (None, [], {}, {'before': '0' * 40}, {'before': 'a' * 39},
                      {'before': '--help'}, {'before': 'a' * 40 + ';echo unsafe'},
                      {'before': 123}, {'before': 'a' * 40 + '\n'}):
            self.assertEqual(dispatch.command('push', event), full)
        for event in ({}, {'pull_request': None}, {'pull_request': []},
                      {'pull_request': {'base': 'invalid'}}, {'pull_request': {'base': {}}}):
            self.assertEqual(dispatch.command('pull_request', event), full)

    def test_main_uses_argv_propagates_failure_and_does_not_run_a_shell(self):
        with tempfile.TemporaryDirectory() as folder:
            event = Path(folder) / 'event.json'
            event.write_text(json.dumps({'before': 'c' * 40}), encoding='utf-8')
            with patch.object(dispatch.subprocess, 'run', return_value=subprocess.CompletedProcess([], 7)) as run:
                self.assertEqual(dispatch.main({'GITHUB_EVENT_NAME': 'push', 'GITHUB_EVENT_PATH': str(event)}), 7)
            args, kwargs = run.call_args
            self.assertIsInstance(args[0], list)
            self.assertEqual(args[0][-2:], ['--changed-from', 'c' * 40])
            self.assertNotIn('shell', kwargs)
            event.write_text('{broken', encoding='utf-8')
            with patch.object(dispatch.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
                dispatch.main({'GITHUB_EVENT_NAME': 'push', 'GITHUB_EVENT_PATH': str(event)})
            self.assertNotIn('--changed-from', run.call_args.args[0])
        with patch.object(dispatch.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
            dispatch.main({})
        self.assertNotIn('--changed-from', run.call_args.args[0])

    def test_workflow_keeps_full_catalog_check_before_builders(self):
        workflow = (dispatch.ROOT / '.github/workflows/validate-experiments.yml').read_text(encoding='utf-8')
        self.assertIn('python scripts/ci_experiment_bundles.py', workflow)
        self.assertIn('python tests/test_bundle_ci_dispatch.py', workflow)
        self.assertIn('workflow_dispatch:', workflow)
        self.assertLess(workflow.index('python scripts/check_download_catalog.py'),
                        workflow.index('python scripts/build_experiments.py'))


if __name__ == '__main__':
    unittest.main()
