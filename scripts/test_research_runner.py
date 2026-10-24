"""Real subprocess checks for the portable, declarative local runner."""
import copy
import hashlib
import importlib.util
import json
import itertools
import random
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / 'tools/research_runner.py'
spec = importlib.util.spec_from_file_location('research_runner', RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
RUNES = [chr(0x16A0 + i) for i in range(29)]


def signed(task):
    task = copy.deepcopy(task)
    raw = json.dumps({k: v for k, v in task.items() if k != 'taskId'},
                     ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    task['taskId'] = hashlib.sha256(raw).hexdigest()
    return task


def fixture(values=(0, 1, 2, 3), steps=None, criterion=None):
    return signed({'schema': runner.TASK_SCHEMA, 'engine': runner.ENGINE,
                   'title': 'Synthetic local control', 'pages': [{'id': 'lp2-15', 'text': ''.join(RUNES[v] for v in values)}],
                   'alphabet': [{'rune': r, 'latin': 'label' + str(i), 'prime': i + 2} for i, r in enumerate(RUNES)],
                   'steps': steps or [], 'criterion': criterion or {'kind': 'measurement'}})


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='local-rune-runner-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def execute(self, task, name='result.json', success=True):
        path = self.root / 'task.json'
        path.write_bytes(json.dumps(task, ensure_ascii=False, indent=2).encode('utf-8'))
        before = path.read_bytes()
        output = self.root / name
        result = subprocess.run([sys.executable, str(RUNNER), '--task', str(path), '--out', str(output)],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stderr)
        self.assertEqual(path.read_bytes(), before, 'Task is immutable')
        if success:
            return json.loads(output.read_bytes())
        self.assertFalse(output.exists(), result.stderr)

    def values(self, result):
        return [[RUNES.index(c) for c in row['text'] if c in RUNES] for row in result['transformed']]

    def test_mixed_ordered_operations_and_prefix_positive_negative(self):
        task = fixture(steps=[{'op': 'reverse', 'unit': 'page'}, {'op': 'affine', 'a': 2, 'b': 1},
                              {'op': 'cumulative-difference', 'reset': 'page'}],
                       criterion={'kind': 'exact-prefix', 'values': [7, 27, 27, 27]})
        result = self.execute(task)
        self.assertEqual(self.values(result), [[7, 27, 27, 27]])
        self.assertEqual(result['matches'], [{'page': 'lp2-15', 'matched': True}])
        self.assertEqual(result['metrics']['equalAdjacentPairs'], 2)
        task['criterion']['values'] = [7, 27, 27, 27, 0]
        result = self.execute(signed(task), 'negative.json')
        self.assertFalse(result['matches'][0]['matched'])

    def test_reverse_units_retain_all_separator_positions(self):
        task = fixture()
        text = RUNES[0] + RUNES[1] + ' / ' + RUNES[2] + '\r\n' + RUNES[3] + RUNES[4] + '!'
        task['pages'][0]['text'] = text
        for unit, expected in [('word', [1, 0, 2, 4, 3]), ('line', [2, 1, 0, 4, 3]), ('page', [4, 3, 2, 1, 0])]:
            task['steps'] = [{'op': 'reverse', 'unit': unit}]
            result = self.execute(signed(task), unit + '.json')
            self.assertEqual(self.values(result), [expected])
            output = result['transformed'][0]['text']
            self.assertEqual([(i, c) for i, c in enumerate(output) if c not in RUNES],
                             [(i, c) for i, c in enumerate(text) if c not in RUNES])

    def test_cumulative_resets_and_page_isolation(self):
        task = fixture()
        task['pages'] = [{'id': 'lp1-00', 'text': RUNES[2] + ' ' + RUNES[5] + '\n' + RUNES[9]},
                         {'id': 'lp2-01', 'text': RUNES[4]}]
        for reset, expected in [('page', [2, 3, 4]), ('line', [2, 3, 9]), ('word', [2, 5, 9])]:
            task['steps'] = [{'op': 'cumulative-difference', 'reset': reset}]
            result = self.execute(signed(task), reset + '.json')
            self.assertEqual(self.values(result), [expected, [4]])
            self.assertEqual(result['matches'], [])

    def test_metrics_empty_and_page_boundaries(self):
        task = fixture((0, 0, 1))
        task['pages'].extend([{'id': 'lp2-16', 'text': RUNES[1]}, {'id': 'lp2-17', 'text': ' ;\n'}])
        result = self.execute(signed(task))
        self.assertEqual(result['metrics'], {'pages': 3, 'runes': 4, 'adjacentPairs': 2,
                                             'equalAdjacentPairs': 1, 'ioc': 1 / 3})
        empty = self.execute(fixture(()), 'empty.json')
        self.assertEqual(empty['metrics']['ioc'], 0)
        self.assertEqual(empty['matches'], [])

    def test_deterministic_bytes_and_no_input_mutation(self):
        task = fixture(steps=[{'op': 'affine', 'a': 0, 'b': 28}])
        before = copy.deepcopy(task)
        self.execute(task, 'one.json'); self.execute(task, 'two.json')
        self.assertEqual((self.root / 'one.json').read_bytes(), (self.root / 'two.json').read_bytes())
        self.assertEqual(task, before)
        self.assertEqual(runner.run(task)['metrics']['ioc'], 1)

    def test_tampered_identity_rejected_before_output(self):
        task = fixture()
        task['pages'][0]['text'] += RUNES[0]
        self.execute(task, success=False)

    def test_unknown_fields_code_operations_and_bad_bounds_rejected(self):
        mutations = [lambda t: t.update(command='echo unsafe'),
                     lambda t: t.update(steps=[{'op': 'exec', 'code': 'print(1)'}]),
                     lambda t: t.update(steps=[{'op': 'affine', 'a': True, 'b': 0}]),
                     lambda t: t.update(steps=[{'op': 'affine', 'a': 29, 'b': 0}]),
                     lambda t: t.update(steps=[{'op': 'reverse', 'unit': 'page', 'code': ''}]),
                     lambda t: t.update(steps=[{'op': 'reverse', 'unit': 'page'}] * 9),
                     lambda t: t.update(criterion={'kind': 'exact-prefix', 'values': [29]}),
                     lambda t: t.update(criterion={'kind': 'measurement', 'values': []}),
                     lambda t: t.update(pages=[{'id': 'lp2-' + str(i).zfill(2), 'text': ''} for i in range(76)]),
                     lambda t: t['pages'].append(copy.deepcopy(t['pages'][0])),
                     lambda t: t['pages'][0].update(id='../bad'),
                     lambda t: t['pages'][0].update(id='lp1-17'),
                     lambda t: t['pages'][0].update(id='lp2-58'),
                     lambda t: t['alphabet'][1].update(rune=RUNES[0]),
                     lambda t: t['alphabet'][0].update(latin='x' * 9),
                     lambda t: t['alphabet'][0].update(prime=1),
                     lambda t: t['alphabet'][0].update(prime=1000001),
                     lambda t: t['alphabet'].pop(),
                     lambda t: t.update(title='x' + ' ' * 300),
                     lambda t: t.update(criterion={'kind': 'exact-prefix', 'values': [0] * 257}),
                     lambda t: t['pages'][0].update(text='.' * 300001),
                     lambda t: t['pages'][0].update(text=RUNES[0] * 20001)]
        for i, mutate in enumerate(mutations):
            with self.subTest(case=i):
                task = fixture(); mutate(task)
                self.execute(signed(task), str(i) + '.json', success=False)

    def test_output_refuses_existing_task_and_script(self):
        task = fixture()
        path = self.root / 'task.json'; path.write_text(json.dumps(task), encoding='utf-8')
        existing = self.root / 'existing.json'; existing.write_bytes(b'Preserve me')
        runner_before = RUNNER.read_bytes()
        for target in (path, existing, RUNNER):
            with self.subTest(target=target):
                before = target.read_bytes()
                result = subprocess.run([sys.executable, str(RUNNER), '--task', str(path), '--out', str(target)],
                                        cwd=self.root, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(target.read_bytes(), before)
        self.assertEqual(RUNNER.read_bytes(), runner_before)

    def test_duplicate_json_fields_nonfinite_values_and_oversized_input_rejected(self):
        valid = json.dumps(fixture())
        examples = [valid.replace('"title":', '"title":"injected", "title":', 1),
                    valid.replace('"steps": []', '"steps": NaN'),
                    ' ' * (runner.MAX_FILE_BYTES + 1)]
        for i, raw in enumerate(examples):
            with self.subTest(case=i):
                path = self.root / 'invalid.json'
                path.write_text(raw, encoding='utf-8')
                output = self.root / ('invalid-' + str(i) + '.json')
                result = subprocess.run([sys.executable, str(RUNNER), '--task', str(path), '--out', str(output)],
                                        cwd=self.root, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())

    def test_codepoint_limits_allow_astral_separator_and_labels(self):
        task = fixture()
        task['title'] = '\U0001f9ea' * 300
        task['alphabet'][0]['latin'] = '\U0001f9ea' * 8
        task['pages'][0]['text'] = '\U0001f9ea' * 300000
        result = self.execute(signed(task))
        self.assertEqual(result['metrics']['runes'], 0)
        self.assertEqual(result['transformed'][0]['text'], task['pages'][0]['text'])

    def test_keyed_shift_independent_hand_vectors(self):
        expected = {
            ('repeat', 'subtract'): [0, 0, 2, 2, 4, 4],
            ('plaintext-autokey', 'subtract'): [0, 0, 3, 4, 2, 2],
            ('ciphertext-autokey', 'subtract'): [0, 0, 2, 2, 2, 2],
            ('repeat', 'add'): [2, 4, 4, 6, 6, 8],
            ('plaintext-autokey', 'add'): [2, 4, 5, 8, 10, 14],
            ('ciphertext-autokey', 'add'): [2, 4, 4, 6, 8, 10],
        }
        for (mode, direction), values in expected.items():
            with self.subTest(mode=mode, direction=direction):
                task = fixture((1, 2, 3, 4, 5, 6), steps=[{'op': 'keyed-shift', 'key': [1, 2],
                                'mode': mode, 'direction': direction, 'reset': 'page'}])
                self.assertEqual(self.values(self.execute(task, mode + direction + '.json')), [values])

    def test_keyed_shift_separators_resets_pages_and_current_step_input(self):
        task = fixture()
        original = RUNES[2] + RUNES[5] + ' / ' + RUNES[9] + RUNES[10] + '\r\n' + RUNES[7]
        task['pages'] = [{'id': 'lp2-15', 'text': original},
                         {'id': 'lp2-16', 'text': RUNES[3] + RUNES[6]}]
        for reset, expected in [('page', [1, 4, 5, 5, 2]), ('line', [1, 4, 5, 5, 6]),
                                ('word', [1, 4, 8, 2, 6])]:
            task['steps'] = [{'op': 'keyed-shift', 'key': [1], 'mode': 'plaintext-autokey',
                              'direction': 'subtract', 'reset': reset}]
            result = self.execute(signed(task), 'keyed-' + reset + '.json')
            self.assertEqual(self.values(result), [expected, [2, 4]])
            self.assertEqual([(i, ch) for i, ch in enumerate(result['transformed'][0]['text']) if ch not in RUNES],
                             [(i, ch) for i, ch in enumerate(original) if ch not in RUNES])
        # After affine, the input C to this step is [3,5,7], so C-C(previous)=[2,2,2].
        task = fixture((1, 2, 3), steps=[{'op': 'affine', 'a': 2, 'b': 1},
                       {'op': 'keyed-shift', 'key': [1], 'mode': 'ciphertext-autokey',
                        'direction': 'subtract', 'reset': 'page'}])
        self.assertEqual(self.values(self.execute(task, 'pipeline.json')), [[2, 2, 2]])

    def test_keyed_shift_rejects_unknown_fields_bool_keys_and_invalid_bounds(self):
        base = {'op': 'keyed-shift', 'key': [1], 'mode': 'repeat',
                'direction': 'subtract', 'reset': 'page'}
        invalid = [{'key': []}, {'key': [1] * 257}, {'key': [True]}, {'key': [False]},
                   {'key': [-1]}, {'key': [29]}, {'key': 'ABC'}, {'key': [1.5]},
                   {'mode': 'autokey'}, {'direction': 'both'}, {'reset': 'book'},
                   {'phase': 1}, {'code': 'print(1)'}, {'key': [None]}]
        for i, patch in enumerate(invalid):
            with self.subTest(patch=patch):
                self.execute(fixture(steps=[{**base, **patch}]), 'bad-key-' + str(i) + '.json', success=False)

    def test_keyed_shift_all_modes_directions_resets_cross_runtime_complete_results(self):
        rng = random.Random(33012410)
        long_run = ''.join(RUNES[rng.randrange(29)] for _ in range(600))
        text = long_run + ' / ' + RUNES[3] + RUNES[4] + '\r\n' + RUNES[8] + '\t' + RUNES[2]
        tasks = []
        for mode, direction, reset, size in itertools.product(
                ('repeat', 'plaintext-autokey', 'ciphertext-autokey'),
                ('subtract', 'add'), ('page', 'line', 'word'), (1, 2, 256)):
            task = fixture(steps=[{'op': 'keyed-shift', 'key': [(7 * i + 3) % 29 for i in range(size)],
                                   'mode': mode, 'direction': direction, 'reset': reset}])
            task['pages'] = [{'id': 'lp2-15', 'text': text}, {'id': 'lp2-16', 'text': RUNES[4] * 3},
                             {'id': 'lp2-17', 'text': ' /\r\n'}]
            tasks.append(signed(task))
        code = "const E=require(process.argv[1]);const fs=require('node:fs');const tasks=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(tasks.map(t=>E.run(t))));"
        output = subprocess.run(['node', '-e', code, str(RUNNER.parents[1] / 'local-experiment.js')],
                                input=json.dumps(tasks, ensure_ascii=False), capture_output=True,
                                text=True, encoding='utf-8', timeout=30)
        self.assertEqual(output.returncode, 0, output.stderr)
        js = json.loads(output.stdout)
        self.assertEqual(len(js), 54)
        self.assertEqual(js, [runner.run(task) for task in tasks])

    def test_shared_javascript_and_python_runtime_parity(self):
        root = RUNNER.parents[1]
        result = subprocess.run(['node', 'scripts/test_local_experiment.cjs'],
                                cwd=root, capture_output=True, text=True,
                                encoding='utf-8', timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_optional_reproduction_package(self):
        result = subprocess.run(['node', 'scripts/test_local_run_package.cjs'],
                                cwd=RUNNER.parents[1], capture_output=True, text=True,
                                encoding='utf-8', timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
