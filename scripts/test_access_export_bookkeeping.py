"""Exercise export bookkeeping without executing the export builder."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


BUILDER = Path(__file__).with_name('build_access_exports.py')


class BookkeepingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.tree = ast.parse(BUILDER.read_text(encoding='utf-8'))
        # Extract only pure local helpers; importing this script would rebuild exports.
        helpers = [node for node in self.tree.body
                   if isinstance(node, ast.FunctionDef) and node.name in ('read', 'save', 'register')]
        self.env = {'root': self.root, 'base': 'https://example.test/',
                    'json': json, 'hashlib': hashlib, 'files': [], 'registered_paths': set()}
        exec(compile(ast.Module(body=helpers, type_ignores=[]), str(BUILDER), 'exec'), self.env)

    def test_save_preserves_exact_utf8_bytes_and_skips_unchanged_writes(self):
        text = 'Rune \u16a0 and \u2014\nSecond line\n'
        self.env['save']('nested/output.txt', text)
        output = self.root / 'nested/output.txt'
        self.assertEqual(output.read_bytes(), text.encode('utf-8'))
        before = output.stat().st_mtime_ns
        with patch.object(Path, 'write_bytes', side_effect=AssertionError('unchanged file rewritten')):
            self.env['save']('nested/output.txt', text)
        self.assertEqual(output.stat().st_mtime_ns, before)
        self.env['save']('nested/output.txt', text + 'Changed\n')
        self.assertEqual(output.read_bytes(), (text + 'Changed\n').encode('utf-8'))

    def test_crlf_existing_output_is_replaced_by_proposed_lf_bytes(self):
        output = self.root / 'output.txt'
        output.write_bytes(b'one\r\ntwo\r\n')
        self.env['save']('output.txt', 'one\ntwo\n')
        self.assertEqual(output.read_bytes(), b'one\ntwo\n')
        # Match the former write_text(newline='\n') contract: do not silently
        # normalize CRLF already present inside an explicitly supplied string.
        self.env['save']('output.txt', 'one\r\n')
        self.assertEqual(output.read_bytes(), b'one\r\n')

    def test_registered_set_preserves_first_role_and_dependency_order(self):
        for name in ('shared.txt', 'alpha.txt', 'zeta.txt'):
            (self.root / name).write_text(name, encoding='utf-8')
        self.env['register']('shared.txt', 'Canonical existing role', {'id': 'lp2-15', 'release': 'LP2'})
        # Exercise the actual dependency-registration loop with two records.
        loops = [node for node in self.tree.body if isinstance(node, ast.For)
                 and any(isinstance(child, ast.Name) and child.id == 'registered_paths'
                         for child in ast.walk(node))]
        self.assertEqual(len(loops), 1)
        self.env['experiments'] = [
            {'article_path': 'zeta.txt', 'reproduction': {'script': 'alpha.txt',
             'inputs': [{'path': 'shared.txt'}], 'outputs': [{'path': 'zeta.txt'}]}},
            {'article_path': 'shared.txt', 'reproduction': {'script': 'alpha.txt',
             'inputs': [], 'outputs': [{'path': 'zeta.txt'}]}},
        ]
        exec(compile(ast.Module(body=loops, type_ignores=[]), str(BUILDER), 'exec'), self.env)
        rows = self.env['files']
        self.assertEqual([row['path'] for row in rows], ['shared.txt', 'alpha.txt', 'zeta.txt'])
        self.assertEqual(rows[0]['role'], 'Canonical existing role')
        self.assertEqual(rows[0]['page'], 'lp2-15')
        self.assertEqual([row['role'] for row in rows[1:]], ['Experiment file', 'Experiment file'])
        self.assertEqual(self.env['registered_paths'], {row['path'] for row in rows})
        for row in rows:
            raw = (self.root / row['path']).read_bytes()
            self.assertEqual(row['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(row['bytes'], len(raw))

    def test_registry_is_parsed_once_and_same_records_feed_all_three_loops(self):
        calls = [node for node in ast.walk(self.tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name) and node.func.id == 'read'
                 and node.args and isinstance(node.args[0], ast.Constant)
                 and node.args[0].value == 'data/experiments.json']
        self.assertEqual(len(calls), 1)
        assignment = next(node for node in self.tree.body if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == 'experiments'
                                  for target in node.targets))
        calls_seen = []
        records = [{'id': 'first'}, {'id': 'second'}]
        env = {'read': lambda path: calls_seen.append(path) or {'records': records}}
        exec(compile(ast.Module(body=[assignment], type_ignores=[]), str(BUILDER), 'exec'), env)
        self.assertEqual(calls_seen, ['data/experiments.json'])
        self.assertIs(env['experiments'], records)
        loops = [node for node in self.tree.body if isinstance(node, ast.For)
                 and isinstance(node.target, ast.Name) and node.target.id == 'experiment']
        self.assertEqual(len(loops), 3)
        self.assertTrue(all(isinstance(node.iter, ast.Name) and node.iter.id == 'experiments'
                            for node in loops))


if __name__ == '__main__':
    unittest.main()
