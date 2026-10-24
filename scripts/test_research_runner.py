"""Real subprocess checks for the portable, declarative local runner."""
import copy
import hashlib
import importlib.util
import json
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
