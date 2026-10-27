"""Exercise export bookkeeping without executing the export builder."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from reproduction_sources import read_pinned
import archive_reproduction_code as code_archive


BUILDER = Path(__file__).with_name('build_access_exports.py')


class BookkeepingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.tree = ast.parse(BUILDER.read_text(encoding='utf-8'))
        # Extract only pure local helpers; importing this script would rebuild exports.
        helpers = [node for node in self.tree.body
                   if isinstance(node, ast.FunctionDef) and node.name in ('read', 'save', 'register', 'register_unique', 'register_program_binding_object', 'register_receipt_binding_objects', 'reproduction_dependency_paths')]
        self.env = {'root': self.root, 'base': 'https://example.test/',
                    'json': json, 'hashlib': hashlib, 'files': [], 'registered_paths': set(), 'read_pinned': read_pinned}
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

    def test_immutable_explicit_pin_objects_are_validated_and_registered_once(self):
        pins = [{'path': 'local-experiment.js', 'sha256': 'a' * 64}]
        canonical = json.dumps(pins, sort_keys=True, separators=(',', ':')).encode()
        name = 'published-sources/program-bindings/' + hashlib.sha256(canonical).hexdigest() + '.json'
        target = self.root / name
        target.parent.mkdir(parents=True)
        target.write_bytes(canonical + b'\n')
        self.env['register_program_binding_object'](name)
        self.env['register_program_binding_object'](name)
        self.env['register_unique'](name, 'Later duplicate role')
        self.assertEqual(len(self.env['files']), 1)
        self.assertEqual(self.env['files'][0]['role'], 'Declared reproduction pin roles')
        self.assertEqual(self.env['files'][0]['sha256'], hashlib.sha256(canonical + b'\n').hexdigest())
        receipt={'records':[{'provenance':{'sourcePins':[{'path':name,'sha256':hashlib.sha256(canonical+b'\n').hexdigest()}]}}]}
        self.env['register_receipt_binding_objects'](receipt)
        receipt['records'][0]['provenance']['sourcePins'][0]['sha256']='b'*64
        with self.assertRaises(ValueError):self.env['register_receipt_binding_objects'](receipt)
        target.unlink()
        with self.assertRaises(FileNotFoundError):self.env['register_receipt_binding_objects'](receipt)
        for raw in [canonical + b'\n\n', b'[]\n', b'[{"path":"../escape.js","sha256":"' + b'a' * 64 + b'"}]\n']:
            target.write_bytes(raw)
            with self.assertRaises(ValueError):
                self.env['register_program_binding_object'](name)
        self.assertEqual(len(self.env['files']), 1)

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

    def test_retained_input_snapshot_is_downloadable_without_relabeling_current_canonical_bytes(self):
        old=b'{"id":"word-reversal","status":"published","browser_followups":[{"kind":"finite-settings"}],"version":"old"}\n'
        current=b'{"id":"word-reversal","status":"published","browser_followups":[{"kind":"finite-settings"}],"version":"current"}\n'
        digest=hashlib.sha256(old).hexdigest()
        canonical='experiments/records/word-reversal/record.json'
        snapshot='published-sources/records/'+digest+'.json'
        for name,raw in [(canonical,current),(snapshot,old),('article.md',b'article'),('run.py',b'run')]:
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        manifest={'schema':'liberpedia-authored-source-archive-v1','entries':[{'recordId':'word-reversal','sha256':digest,'bytes':len(old),'path':snapshot}]}
        (self.root/'data').mkdir(exist_ok=True)
        (self.root/'data/authored-source-archive.json').write_text(json.dumps(manifest),encoding='utf8')
        pin={'path':canonical,'sha256':digest,'source_path':snapshot}
        experiment={'article_path':'article.md','reproduction':{'script':'run.py','inputs':[pin],'outputs':[]}}
        paths=self.env['reproduction_dependency_paths'](experiment)
        self.assertEqual(paths,sorted(['article.md','run.py',canonical,snapshot]))
        for name in paths:self.env['register'](name,'Experiment file')
        rows={row['path']:row for row in self.env['files']}
        self.assertEqual(rows[canonical]['sha256'],hashlib.sha256(current).hexdigest())
        self.assertEqual(rows[snapshot]['sha256'],digest)
        self.assertEqual(rows[snapshot]['url'],'https://example.test/'+snapshot)
        self.assertEqual(rows[snapshot]['role'],'Experiment file')
        (self.root/canonical).unlink()
        self.assertEqual(self.env['reproduction_dependency_paths'](experiment),sorted(['article.md','run.py',snapshot]))
        (self.root/canonical).write_bytes(current)
        pin['source_path']=canonical
        with self.assertRaises(ValueError):self.env['reproduction_dependency_paths'](experiment)
        pin['source_path']=snapshot
        (self.root/snapshot).write_bytes(b'tampered')
        with self.assertRaises(ValueError):self.env['reproduction_dependency_paths'](experiment)
        self.assertEqual((self.root/canonical).read_bytes(),current)

    def test_retained_code_dependency_registers_old_object_separately_from_current_module(self):
        repository=BUILDER.resolve().parents[1]
        name='local-plan-controls.js';old=b'// old exact code\r\nmodule.exports=1;\r\n';current=b'// current implementation\nmodule.exports=2;\n'
        item=code_archive.entry(name,old)
        for path,raw in [(name,current),(item['path'],old),('article.md',b'article'),('run.py',b'run')]:
            target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        (self.root/'data').mkdir(exist_ok=True)
        (self.root/code_archive.POLICY).write_bytes((repository/code_archive.POLICY).read_bytes())
        (self.root/code_archive.MANIFEST).write_text(json.dumps({'schema':code_archive.SCHEMA,'entries':[item]}),encoding='utf8')
        pin={'path':name,'sha256':item['sha256'],'source_path':item['path']}
        record={'article_path':'article.md','reproduction':{'script':'run.py','inputs':[pin],'outputs':[]}}
        paths=self.env['reproduction_dependency_paths'](record)
        self.assertEqual(paths,sorted(['article.md','run.py',name,item['path']]))
        for path in paths:self.env['register'](path,'Experiment file')
        rows={r['path']:r for r in self.env['files']}
        self.assertEqual(rows[name]['sha256'],hashlib.sha256(current).hexdigest())
        self.assertEqual(rows[item['path']]['sha256'],item['sha256'])
        self.assertEqual(rows[item['path']]['url'],'https://example.test/'+item['path'])
        pin['source_path']=name
        with self.assertRaises(ValueError):self.env['reproduction_dependency_paths'](record)
        self.assertEqual((self.root/name).read_bytes(),current)

    def test_real_earlier_word_reversal_pin_keeps_its_archived_download_path(self):
        repository=BUILDER.resolve().parents[1]
        record=json.loads((repository/'experiments/records/prepared-opening-evidence-gates/record.json').read_text(encoding='utf8'))
        pin=next(p for p in record['reproduction']['inputs'] if p['path']=='experiments/records/lp2-word-reversal/record.json')
        raw,actual=read_pinned(repository,pin)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),pin['sha256'])
        self.assertEqual(actual,'published-sources/records/'+pin['sha256']+'.json')
        compiled={'article_path':'article.md','reproduction':{'script':'run.py','inputs':[{**pin,'source_path':actual}],'outputs':[]}}
        self.env['root']=repository
        self.assertIn(actual,self.env['reproduction_dependency_paths'](compiled))
        self.assertIn(pin['path'],self.env['reproduction_dependency_paths'](compiled))

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
