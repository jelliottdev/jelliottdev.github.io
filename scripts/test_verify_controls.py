"""Synthetic control guard tests; never read or execute manuscript targets."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import research_runner as runner
import verify_controls as guard

ALPHABET = [{'rune': chr(0x16A0 + n), 'latin': 'R' + str(n), 'prime': n + 2} for n in range(29)]


def task(values, criterion, steps=None, page='lp1-01'):
    value = {'schema': runner.TASK_SCHEMA, 'engine': runner.ENGINE,
             'title': 'Synthetic guard fixture', 'alphabet': copy.deepcopy(ALPHABET),
             'pages': [{'id': page, 'text': ''.join(ALPHABET[n]['rune'] for n in values)}],
             'steps': copy.deepcopy(steps or []), 'criterion': copy.deepcopy(criterion)}
    value['taskId'] = runner.task_identity(value)
    return value


def reidentify(value):
    value['taskId'] = runner.task_identity(value)


def document(fixture):
    return {'version': 1, 'origins': [{'origin': {'recordId': 'synthetic-guard', 'followupId': 'known-answer',
            'recordSha256': 'a' * 64, 'protocolSha256': 'b' * 64},
            'control': {'label': 'Synthetic known-answer control', 'task': copy.deepcopy(fixture),
                        'expected_result_sha256': hashlib.sha256(guard.stable(runner.run(fixture)).encode('utf-8')).hexdigest()},
            'question': 'Synthetic guard question', 'scopeChange': 'Synthetic only',
            'limitation': 'No manuscript pass or fail is asserted'}]}


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='synthetic-control-guard-')
        self.folder = Path(self.directory.name)
        (self.folder / 'controls').mkdir()
        self.target = task([8, 9, 10], {'kind': 'measurement'}, page='lp2-15')
        self.fixture = task([0, 1, 2], {'kind': 'exact-prefix', 'values': [0, 1, 2]})

    def tearDown(self):
        self.directory.cleanup()

    def write_control(self, doc):
        fixture = doc['origins'][0]['control']['task']
        (self.folder / 'controls' / (fixture['taskId'] + '.json')).write_text(json.dumps(fixture), encoding='utf-8')

    def verified(self, target, doc):
        self.write_control(doc)
        calls = []
        original = runner.run
        def observe(value):
            calls.append(value['taskId'])
            self.assertNotEqual(value['taskId'], target['taskId'], 'Target must not run in control verification')
            return original(value)
        with patch.object(runner, 'run', observe):
            count = guard.verified_controls(target, doc, self.folder)
        return count, calls

    def test_measurement_accepts_same_program_prefix_control_only(self):
        doc = document(self.fixture)
        count, calls = self.verified(self.target, doc)
        self.assertEqual(count, 1)
        self.assertEqual(calls, [self.fixture['taskId']])
        bad = task([0, 1, 2], {'kind': 'measurement'})
        with self.assertRaisesRegex(ValueError, 'exact-prefix control'):
            self.verified(self.target, document(bad))
        stats = task([0, 0, 0], {'kind': 'word-affine-count', 'lag': 1, 'a': 1, 'b': 0, 'boundaries': 'non-rune'})
        with self.assertRaisesRegex(ValueError, 'exact-prefix control'):
            self.verified(self.target, document(stats))

    def test_measurement_rejects_partial_prefix_even_with_valid_full_result_hash(self):
        fixture = task([0, 1, 2], {'kind': 'exact-prefix', 'values': [0, 1]})
        with self.assertRaisesRegex(ValueError, 'complete synthetic exact-prefix control'):
            self.verified(self.target, document(fixture))
        # The narrower old prefix protocol remains valid for prefix targets.
        target = task([8, 9, 10], fixture['criterion'], page='lp2-15')
        self.assertEqual(self.verified(target, document(fixture))[0], 1)

    def test_old_prefix_and_statistical_contracts_remain_exact(self):
        target = task([8, 9], self.fixture['criterion'], page='lp2-15')
        self.assertEqual(self.verified(target, document(self.fixture))[0], 1)
        statistical = task([0, 0, 1], {'kind': 'word-affine-count', 'lag': 1, 'a': 1, 'b': 0, 'boundaries': 'non-rune'}, page='lp2-15')
        with self.assertRaisesRegex(ValueError, 'different criterion'):
            self.verified(statistical, document(self.fixture))
        with self.assertRaisesRegex(ValueError, 'different criterion'):
            self.verified(target, document(task([0, 1], {'kind': 'exact-prefix', 'values': [0]})))

    def test_wrong_program_alphabet_empty_or_overbound_controls_reject(self):
        for change, message in [
            (lambda t: t['steps'].append({'op': 'affine', 'a': 1, 'b': 0}), 'different steps'),
            (lambda t: t['alphabet'][0].update(latin='OTHER'), 'different alphabet'),
            (lambda t: t['pages'][0].update(text=''), 'complete synthetic exact-prefix control'),
            (lambda t: t['pages'].append({'id': 'lp1-02', 'text': ''}), 'exceeds its bound'),
            (lambda t: t['pages'][0].update(text=ALPHABET[0]['rune'] * 4097), 'exceeds its bound')]:
            fixture = copy.deepcopy(self.fixture)
            change(fixture)
            reidentify(fixture)
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                self.verified(self.target, document(fixture))
        fixture = copy.deepcopy(self.fixture)
        fixture['criterion']['values'] = []
        reidentify(fixture)
        doc = document(self.fixture)
        doc['origins'][0]['control']['task'] = fixture
        with self.assertRaisesRegex(ValueError, 'prefix'):
            self.verified(self.target, doc)

    def test_full_digest_recovery_and_control_file_are_all_required(self):
        doc = document(self.fixture)
        doc['origins'][0]['control']['expected_result_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'hash differs'):
            self.verified(self.target, doc)
        fixture = task([3, 1, 2], {'kind': 'exact-prefix', 'values': [0, 1, 2]})
        with self.assertRaisesRegex(ValueError, 'recovery property'):
            self.verified(self.target, document(fixture))
        doc = document(self.fixture)
        self.write_control(doc)
        (self.folder / 'controls' / (self.fixture['taskId'] + '.json')).write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'differs from the origin'):
            guard.verified_controls(self.target, doc, self.folder)

    def test_forged_statistical_fraction_cannot_bypass_full_result_hash(self):
        criterion = {'kind': 'word-affine-count', 'lag': 1, 'a': 1, 'b': 1, 'boundaries': 'non-rune'}
        fixture = task([0, 1, 2, 3], criterion)
        target = task([4, 5, 6], criterion, page='lp2-15')
        doc = document(fixture)
        self.assertEqual(self.verified(target, doc)[0], 1)
        forged = runner.run(fixture)
        forged['wordPairs']['expected']['numerator'] = '0'
        doc['origins'][0]['control']['expected_result_sha256'] = hashlib.sha256(guard.stable(forged).encode('utf-8')).hexdigest()
        with self.assertRaisesRegex(ValueError, 'hash differs'):
            self.verified(target, doc)

    def test_main_runs_target_only_after_all_controls_and_never_overwrites(self):
        doc = document(self.fixture)
        self.write_control(doc)
        target_path, origins_path, result_path = [self.folder / n for n in ('task.json', 'origins.json', 'results.json')]
        target_path.write_text(json.dumps(self.target), encoding='utf-8')
        origins_path.write_text(json.dumps(doc), encoding='utf-8')
        arguments = ['verify_controls.py', '--task', str(target_path), '--origins', str(origins_path), '--out', str(result_path)]
        original = runner.run
        calls = []
        def observe(value):
            calls.append(value['taskId'])
            return original(value)
        doc['origins'][0]['control']['expected_result_sha256'] = '0' * 64
        origins_path.write_text(json.dumps(doc), encoding='utf-8')
        with patch.object(sys, 'argv', arguments), patch.object(runner, 'run', observe), self.assertRaises(SystemExit):
            guard.main()
        self.assertEqual(calls, [self.fixture['taskId']])
        self.assertFalse(result_path.exists())
        origins_path.write_text(json.dumps(document(self.fixture)), encoding='utf-8')
        calls.clear()
        with patch.object(sys, 'argv', arguments), patch.object(runner, 'run', observe):
            guard.main()
        self.assertEqual(calls, [self.fixture['taskId'], self.target['taskId']])
        self.assertEqual(json.loads(result_path.read_text(encoding='utf-8')), original(self.target))
        calls.clear()
        with patch.object(sys, 'argv', arguments), patch.object(runner, 'run', observe), self.assertRaises(SystemExit):
            guard.main()
        self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
