"""Full offline synthetic commitments and fail-closed source/geometry checks."""
import copy
import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import browser_followups as fixed
import pinned_domain_controls as controls
import pinned_domain_partitions as P
import rotating_domain_sources as sources


class PinnedDomainControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parents = sources.domains()
        cls.built = {}
        cls.executions = 0
        original = fixed.runner.run
        def synthetic_only(task):
            assert task['title'].startswith('Synthetic complete-output pinned control: d_')
            assert [p['id'] for p in task['pages']] == ['lp1-01']
            assert task['criterion']['kind'] == 'exact-prefix' and len(task['criterion']['values']) == 184
            cls.executions += 1
            return original(task)
        with patch.object(fixed.runner, 'run', side_effect=synthetic_only):
            for variant, parent in cls.parents.items():
                cls.built[variant] = controls.build(controls.ROOT, parent)

    def test_full_two_domains_commit_every_setting_without_target_execution(self):
        self.assertEqual(self.executions, 5122)
        for variant, value in self.built.items():
            manifest, known = value['manifest'], value['template']
            self.assertEqual(set(manifest), {'schema', 'parentDomainId', 'templateSha256', 'encoder', 'sourcePins', 'entries'})
            self.assertEqual(manifest['schema'], controls.SCHEMA)
            self.assertEqual(manifest['encoder'], controls.ENCODER)
            self.assertEqual(manifest['parentDomainId'], P.prepare(self.parents[variant])['domainId'])
            self.assertEqual(len(manifest['entries']), 2561)
            self.assertEqual(len({entry[0] for entry in manifest['entries']}), 2561)
            self.assertTrue(all(len(e) == 2 and all(P.HEX.fullmatch(h) for h in e) for e in manifest['entries']))
            self.assertEqual(manifest['templateSha256'], fixed.digest(known))
            expected_pins = {p['path']: p['sha256'] for p in self.parents[variant]['sourcePins'] + known['sourcePins']}
            self.assertEqual(manifest['sourcePins'], [dict(path=p, sha256=h) for p, h in sorted(expected_pins.items())])
            self.assertTrue(all(p in manifest['sourcePins'] for p in self.parents[variant]['sourcePins']))
            self.assertEqual(known['schema'], controls.TEMPLATE)
            self.assertEqual(len(known['values']), 184)
            self.assertEqual(known['alphabetSha256'], P.ALPHABET)
            self.assertEqual(known['values'][:12], fixed.WARNING12)

    def test_selected_controls_are_exact_stable_and_full_output(self):
        for variant, parent in self.parents.items():
            before = copy.deepcopy(parent)
            for index in (0, 2560):
                value = controls.witness(controls.ROOT, parent, index)
                self.assertEqual(value['entry'], self.built[variant]['manifest']['entries'][index])
                self.assertEqual(value['task']['title'], 'Synthetic complete-output pinned control: '
                                 + self.built[variant]['manifest']['parentDomainId'] + ' setting ' + str(index + 1))
                self.assertEqual(value['result']['transformed'][0]['text'], self.built[variant]['template']['plaintext'])
                self.assertEqual(value['task']['taskId'], fixed.runner.task_identity(value['task']))
            self.assertEqual(parent, before)

    def test_oversized_periods_convert_using_full_parent_geometry_not_selected_page(self):
        parent = self.parents['rotate-left']
        registry = P.MaintainedRegistry()
        keys = registry.resolve({**parent['bank'], 'start': 0, 'count': 1024})
        index = next(i for i, key in enumerate(keys) if len(key) == 324)
        value = controls.witness(controls.ROOT, parent, index)
        self.assertEqual(value['task']['steps'][0], dict(op='finite-shift', key=keys[index], direction='subtract', reset='page'))
        alphabet = fixed.alphabet(controls.ROOT)
        pages = [dict(id='lp2-00', text=alphabet[0]['rune'] * 700)]
        actual = controls.actual_steps(parent, keys[index], pages, alphabet)
        self.assertEqual(actual[0]['key'], keys[index] * 3)
        self.assertEqual(len(actual[0]['key']), 972)
        with self.assertRaisesRegex(ValueError, '20000'):
            controls.actual_steps(parent, [0] * 19999, pages=[dict(id='lp2-00', text=alphabet[0]['rune'] * 20000)], alphabet=alphabet)
        for mode in ('plaintext-autokey', 'ciphertext-autokey'):
            changed = copy.deepcopy(parent)
            changed['steps'][0]['mode'] = mode
            with self.assertRaisesRegex(ValueError, 'autokey'):
                controls.witness(controls.ROOT, changed, index)

    def test_all_source_bundle_parent_and_index_failures_precede_execution(self):
        parent = self.parents['rotate-left']
        bundle = json.loads((controls.ROOT / 'data/local-run-inputs.json').read_bytes())
        with patch.object(fixed.runner, 'run', side_effect=AssertionError('must not execute')):
            for change in (lambda d: d['pages'][-1].update(textSha256='0' * 64),
                           lambda d: d['bank'].update(count=2560),
                           lambda d: d['sourcePins'][0].update(sha256='0' * 64)):
                changed = copy.deepcopy(parent)
                change(changed)
                with self.assertRaises(ValueError):
                    controls.build(controls.ROOT, changed)
            for change in (lambda b: b['alphabet'][0].update(prime=999),
                           lambda b: b['pages'][-1].update(raw='unselected page changed')):
                changed = copy.deepcopy(bundle)
                change(changed)
                with self.assertRaisesRegex(ValueError, 'bundle'):
                    controls.witness(controls.ROOT, parent, 0, bundle=changed)
            for index in (-1, 2561, True, 0.0):
                with self.assertRaises(ValueError):
                    controls.witness(controls.ROOT, parent, index)

    def test_parent_and_actual_source_mutations_during_execution_are_detected(self):
        changed = copy.deepcopy(self.parents['rotate-left'])
        original = fixed.runner.run
        def mutate(task):
            changed['aim']['detail'] += ' altered'
            return original(task)
        with patch.object(fixed.runner, 'run', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'parent changed'):
                controls.witness(controls.ROOT, changed, 0)
        original_pins = controls.source_pins
        calls = 0
        def altered_pins(root, paths):
            nonlocal calls
            value = original_pins(root, paths)
            calls += 1
            if calls > 4:
                value[0]['sha256'] = '0' * 64
            return value
        with patch.object(controls, 'source_pins', side_effect=altered_pins):
            with self.assertRaisesRegex(ValueError, 'source.*changed'):
                controls.witness(controls.ROOT, self.parents['rotate-left'], 0)

    def test_cli_rejects_output_outside_dedicated_qa_temp_before_work(self):
        result = subprocess.run(['python', 'scripts/pinned_domain_controls.py', '--output-dir', '.'],
                                cwd=controls.ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('qa-temp', result.stderr)

    def test_cli_artifacts_use_exact_utf8_lf_and_report_raw_manifest_hash(self):
        qa_root = (controls.ROOT / 'qa-temp').resolve()
        qa_root.mkdir(exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix='pinned-controls-cli-', dir=qa_root)).resolve()
        self.assertTrue(output.is_relative_to(qa_root) and output != qa_root)
        try:
            stream = io.StringIO()
            # Full5122 controls are covered above. Reuse those genuine results
            # here to test serialization without executing all witnesses twice.
            with patch.object(sys, 'argv', ['pinned_domain_controls.py', '--output-dir', str(output)]), \
                    patch.object(sources, 'domains', return_value=self.parents), \
                    patch.object(controls, 'build', side_effect=lambda root, parent: copy.deepcopy(
                        self.built[next(v for v, p in self.parents.items() if p == parent)])), \
                    contextlib.redirect_stdout(stream):
                controls.main()
            report = json.loads(stream.getvalue())
            for item in report:
                raw = (output / (item['variant'] + '-controls.json')).read_bytes()
                self.assertEqual(raw, (P.stable(self.built[item['variant']]['manifest']) + '\n').encode('utf-8'))
                self.assertTrue(raw.endswith(b'\n') and b'\r\n' not in raw)
                self.assertEqual(item['manifestSha256'], hashlib.sha256(raw).hexdigest())
            raw = (output / 'warning-template.json').read_bytes()
            self.assertTrue(raw.endswith(b'\n') and b'\r\n' not in raw)
            self.assertTrue(all(item['templateSha256'] == fixed.digest(json.loads(raw)) for item in report))
        finally:
            resolved = output.resolve()
            self.assertTrue(resolved.is_relative_to(qa_root) and resolved != qa_root)
            shutil.rmtree(resolved)


if __name__ == '__main__':
    unittest.main()
