"""Invented isolated programs only; no historical experiment is executed."""
import copy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from retained_bundle_checks import parse_checks, run_checks, TIMEOUT, MAX_FILE_BYTES


class RetainedChecksTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inventory = {}
        self.python = 'experiments/records/invented/run.py'
        self.node = 'scripts/retained-check.mjs'
        self.output = 'experiments/records/invented/retained.json'
        self.put(self.python, b'import sys\nassert sys.argv[1:]==["--check"]\nprint("python okay")\n')
        self.put(self.node, b'import fs from "node:fs";if(process.argv[2]!=="--check")throw Error("flag");JSON.parse(fs.readFileSync(process.argv[3],"utf8"));console.log("node okay");\n')
        self.put(self.output, b'{"invented":true}\n')
        self.record = {'id': 'invented', 'published_program_collections': [{'output': self.output}],
            'reproduction': {'script': self.python, 'script_sha256': self.inventory[self.python]['sha256'],
                'inputs': [self.pin(self.node)], 'outputs': [self.pin(self.output)],
                'command': 'python ' + self.python + ' --check && node ' + self.node + ' --check ' + self.output}}

    def put(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        self.inventory[name] = {'path': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

    def pin(self, path):
        return {'path': path, 'sha256': self.inventory[path]['sha256']}

    def test_exact_commands_execute_in_extraction_without_shell_and_both_declaration_kinds_work(self):
        parsed = parse_checks(self.record, self.inventory)
        self.assertEqual(len(parsed), 2)
        results = run_checks(self.root, self.record, self.inventory)
        self.assertIn('python okay', results[0].stdout)
        self.assertIn('node okay', results[1].stdout)
        self.record['published_programs'] = self.record.pop('published_program_collections')
        self.record['reproduction']['command'] = self.record['reproduction']['command'].replace('python ', 'python3 ', 1)
        calls = []
        run_checks(self.root, self.record, self.inventory, run=lambda argv, **kwargs: calls.append((argv, kwargs)))
        self.assertEqual(calls[0][0][0], sys.executable)
        self.assertEqual(calls[1][0][0], 'node')
        for _, options in calls:
            self.assertEqual(options['cwd'], self.root.resolve())
            self.assertFalse(options['shell'])
            self.assertTrue(options['check'])
            self.assertEqual(options['env']['PYTHONDONTWRITEBYTECODE'], '1')

    def test_shell_arguments_writes_environment_substitutions_and_traversal_are_rejected(self):
        valid = self.record['reproduction']['command']
        for command in [valid + ' &&', valid + ' ; echo x', valid.replace('--check', '--write', 1),
            valid.replace('--check', '--check --extra', 1), 'X=1 ' + valid, 'node -e "exit()"',
            valid.replace(self.node, '../escape.mjs'), valid.replace(self.node, 'scripts/./retained-check.mjs'),
            valid.replace(self.node, 'scripts//retained-check.mjs'), valid.replace(self.python, '$(pwd)/run.py'),
            valid.replace(self.python, '`echo run.py`'), valid.replace(self.python, '"' + self.python + '"'),
            valid.replace(' && ', '\n'), valid + ' > output.txt', ' && '.join([valid.split(' && ')[0]] * 5)]:
            record = copy.deepcopy(self.record)
            record['reproduction']['command'] = command
            with self.subTest(command=command), self.assertRaises(ValueError):
                parse_checks(record, self.inventory)

    def test_all_scripts_and_optional_outputs_need_exact_declaration_and_inventory_pins(self):
        for mutate in [lambda r: r['reproduction']['inputs'].clear(),
                       lambda r: r['reproduction']['outputs'].clear(),
                       lambda r: r['reproduction']['inputs'][0].update(sha256='0' * 64),
                       lambda r: r['reproduction'].update(command='node ' + self.node + ' --check ' + self.output),
                       lambda r: r['reproduction'].update(command='python ' + self.node + ' --check'),
                       lambda r: r.pop('published_program_collections')]:
            record = copy.deepcopy(self.record)
            mutate(record)
            with self.assertRaises(ValueError):
                parse_checks(record, self.inventory)
        inventory = copy.deepcopy(self.inventory)
        del inventory[self.node]
        with self.assertRaises(ValueError):
            parse_checks(self.record, inventory)
        (self.root / self.node).unlink()
        with self.assertRaises(ValueError):
            run_checks(self.root, self.record, self.inventory)

    def test_corrupted_selected_bytes_are_refused_before_any_command(self):
        (self.root / self.output).write_bytes(b'{"invented":false}\n')
        with self.assertRaisesRegex(ValueError, 'size|SHA-256'):
            run_checks(self.root, self.record, self.inventory,
                       run=lambda *args, **kwargs: self.fail('No process before byte verification'))

    def test_inventory_lengths_and_repeated_pins_are_strictly_bounded(self):
        for size in [True, -1, MAX_FILE_BYTES + 1]:
            inventory = copy.deepcopy(self.inventory)
            inventory[self.node]['bytes'] = size
            with self.assertRaises(ValueError):
                parse_checks(self.record, inventory)
        record = copy.deepcopy(self.record)
        record['reproduction']['inputs'].append(copy.deepcopy(record['reproduction']['inputs'][0]))
        with self.assertRaises(ValueError):
            parse_checks(record, self.inventory)

    def test_runtime_unlisted_filesystem_dependency_propagates_node_enoent(self):
        self.put(self.node, b'import fs from "node:fs";fs.readFileSync("data/unlisted-runtime.json");\n')
        self.record['reproduction']['inputs'] = [self.pin(self.node)]
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            run_checks(self.root, self.record, self.inventory)
        self.assertIn('ENOENT', caught.exception.stderr)
        self.assertFalse((self.root / 'data/unlisted-runtime.json').exists())

    def test_abnormal_replay_and_timeouts_never_become_success(self):
        self.put(self.python, b'raise SystemExit(7)\n')
        self.record['reproduction']['script_sha256'] = self.inventory[self.python]['sha256']
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            run_checks(self.root, self.record, self.inventory)
        self.assertEqual(caught.exception.returncode, 7)
        def timeout(argv, **options):
            raise subprocess.TimeoutExpired(argv, options['timeout'])
        with self.assertRaises(subprocess.TimeoutExpired):
            run_checks(self.root, self.record, self.inventory, run=timeout)

    def test_deadline_is_shared_across_commands_not_restarted(self):
        times = iter([0, 1, TIMEOUT + 1])
        calls = []
        with self.assertRaises(subprocess.TimeoutExpired):
            run_checks(self.root, self.record, self.inventory,
                       monotonic=lambda: next(times), run=lambda *args, **options: calls.append(options))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['timeout'], TIMEOUT - 1)


if __name__ == '__main__':
    unittest.main()
