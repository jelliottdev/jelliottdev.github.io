"""Historical record dependencies keep exact reviewed bytes and original ZIP names."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from archive_authored_sources import entry
import archive_reproduction_code as code_archive
from reproduction_sources import read_pinned
from build_experiment_bundles import build as bundle

ROOT = Path(__file__).resolve().parents[1]
OLD_PATH = 'published-sources/records/9bb0e98cd3ce2e696871d6aa0a0f6854690e303213d8d6539dda9d157447bafe.json'
NAME = 'experiments/records/lp2-word-reversal/record.json'
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


class ReproductionSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old = (ROOT / OLD_PATH).read_bytes()
        self.item = entry(self.old)
        self.current = self.old + b'\n'
        self.put(NAME, self.current)
        self.put(self.item['path'], self.old)
        self.manifest = {'schema': 'liberpedia-authored-source-archive-v1', 'entries': [self.item]}
        self.put('data/authored-source-archive.json', self.manifest)
        self.pin = {'path': NAME, 'sha256': SHA(self.old)}

    def tearDown(self):
        self.temp.cleanup()

    def put(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value if isinstance(value, bytes) else json.dumps(value).encode())

    def test_current_exact_first_and_old_dependency_preserve_two_independent_versions(self):
        self.assertEqual(read_pinned(self.root, {'path': NAME, 'sha256': SHA(self.current)}), (self.current, NAME))
        self.assertEqual(read_pinned(self.root, self.pin), (self.old, self.item['path']))
        (self.root / 'data/authored-source-archive.json').unlink()
        self.assertEqual(read_pinned(self.root, {'path': NAME, 'sha256': SHA(self.current)}), (self.current, NAME))
        with self.assertRaises(ValueError):
            read_pinned(self.root, self.pin)
        self.assertEqual((self.root / NAME).read_bytes(), self.current)

    def test_no_fallback_for_scientific_files_or_caller_source_path_overrides(self):
        science = 'experiments/records/example/results.json'
        self.put(science, b'changed scientific output')
        for pin in [{'path': science, 'sha256': SHA(self.old)}, {**self.pin, 'source_path': self.item['path']},
                    {'path': '../escape', 'sha256': SHA(self.old)}, {'path': NAME, 'sha256': [SHA(self.old)]}]:
            with self.assertRaises(ValueError):
                read_pinned(self.root, pin)

    def test_missing_corrupt_repeated_and_misattributed_archive_entries_fail(self):
        for change in ['corrupt', 'missing', 'duplicate', 'owner', 'path', 'bytes', 'unlisted']:
            with self.subTest(change=change):
                manifest = copy.deepcopy(self.manifest)
                self.put(self.item['path'], self.old)
                if change == 'corrupt':
                    self.put(self.item['path'], self.old[:-1] + b' ')
                elif change == 'missing':
                    (self.root / self.item['path']).unlink()
                elif change == 'duplicate':
                    manifest['entries'].append(copy.deepcopy(self.item))
                elif change == 'owner':
                    manifest['entries'][0]['recordId'] = 'different-record'
                elif change == 'path':
                    manifest['entries'][0]['path'] = '../outside.json'
                elif change == 'bytes':
                    manifest['entries'][0]['bytes'] += 1
                else:
                    manifest['entries'] = []
                self.put('data/authored-source-archive.json', manifest)
                with self.assertRaises((ValueError, json.JSONDecodeError)):
                    read_pinned(self.root, self.pin)

    def test_reproduction_bundle_uses_old_bytes_at_original_path_and_ignores_derived_hint(self):
        base = 'experiments/records/dependent'
        self.put(base + '/record.json', b'{"id":"dependent"}')
        self.put(base + '/article.md', b'Published dependent account')
        self.put(base + '/run.py', b'print("fixture only")\n')
        self.put('scripts/verify_bundle.py', b'# fixture verifier source\n')
        record = {'id': 'dependent', 'title': 'Dependent fixture', 'question': 'Keep exact source version?',
                  'outcome': 'inconclusive', 'finding': 'Fixture', 'limitations': 'Fixture only',
                  'article_path': base + '/article.md',
                  'review': {'reviewer': 'Fixture reviewer', 'retested_on': '2026-10-26'},
                  'reproduction': {'script': base + '/run.py', 'script_sha256': SHA((self.root / (base + '/run.py')).read_bytes()),
                                   'command': 'python ' + base + '/run.py', 'environment': 'Python',
                                   'inputs': [{**self.pin, 'source_path': 'untrusted/not-authority.json'}], 'outputs': []}}
        path, _, _ = bundle(self.root, record)
        with zipfile.ZipFile(self.root / path) as saved:
            self.assertEqual(saved.read(NAME), self.old)
            self.assertNotIn(self.item['path'], saved.namelist())
        self.assertEqual((self.root / NAME).read_bytes(), self.current)
        self.assertEqual(record['reproduction']['inputs'][0]['sha256'], SHA(self.old))

    def retained_code(self):
        name='local-plan-controls.js'
        old=b'// preserved implementation\r\nmodule.exports={version:1};\r\n'
        current=old.replace(b'\r\n',b'\n')+b'// private code upgrade\n'
        item=code_archive.entry(name,old)
        self.put(name,current)
        self.put(item['path'],old)
        self.put(code_archive.POLICY,(ROOT/code_archive.POLICY).read_bytes())
        self.put(code_archive.MANIFEST,{'schema':code_archive.SCHEMA,'entries':[item]})
        return name,old,current,item,{'path':name,'sha256':SHA(old)}

    def test_maintained_code_fallback_is_raw_byte_exact_including_crlf_and_missing_current(self):
        name,old,current,item,pin=self.retained_code()
        self.assertEqual(read_pinned(self.root,pin),(old,item['path']))
        self.assertEqual(read_pinned(self.root,{'path':name,'sha256':SHA(current)}),(current,name))
        self.assertNotEqual(SHA(old),SHA(old.replace(b'\r\n',b'\n')))
        with self.assertRaises(ValueError):read_pinned(self.root,{'path':name,'sha256':SHA(old.replace(b'\r\n',b'\n'))})
        (self.root/name).unlink()
        self.assertEqual(read_pinned(self.root,pin),(old,item['path']))
        self.assertEqual((self.root/item['path']).read_bytes(),old)

    def test_code_archive_cannot_fall_back_science_unlisted_modules_or_other_source_associations(self):
        name,old,current,item,pin=self.retained_code()
        for path in ['experiments/records/example/results.json','experiments/records/example/plan.json','scripts/unlisted-module.mjs']:
            self.put(path,b'changed')
            with self.assertRaises(ValueError):read_pinned(self.root,{'path':path,'sha256':SHA(old)})
        with self.assertRaises(ValueError):read_pinned(self.root,{**pin,'source_path':item['path']})
        policy=json.loads((ROOT/code_archive.POLICY).read_bytes());policy['paths'].remove(name);self.put(code_archive.POLICY,policy)
        with self.assertRaises(ValueError):read_pinned(self.root,pin)
        self.put(code_archive.POLICY,(ROOT/code_archive.POLICY).read_bytes())
        wrong={**item,'sourcePath':'local-experiment.js'}
        self.put(code_archive.MANIFEST,{'schema':code_archive.SCHEMA,'entries':[wrong]})
        with self.assertRaises(ValueError):read_pinned(self.root,pin)
        self.put(code_archive.MANIFEST,{'schema':code_archive.SCHEMA,'entries':[item]})
        self.put(item['path'],old+b'tampered')
        with self.assertRaises(ValueError):read_pinned(self.root,pin)
        self.assertEqual((self.root/name).read_bytes(),current)

    def test_offline_bundle_retains_old_code_at_original_import_path_without_repins(self):
        name,old,current,item,pin=self.retained_code()
        base='experiments/records/code-dependent'
        self.put(base+'/record.json',b'{"id":"code-dependent"}')
        self.put(base+'/article.md',b'Published code fixture')
        self.put(base+'/run.py',b'print("fixture")\n')
        self.put('scripts/verify_bundle.py',b'# fixture verifier\n')
        record={'id':'code-dependent','title':'Old implementation fixture','question':'Preserve exact code?',
                'outcome':'inconclusive','finding':'Fixture','limitations':'Fixture only','article_path':base+'/article.md',
                'review':{'reviewer':'Fixture','retested_on':'2026-10-27'},
                'reproduction':{'script':base+'/run.py','script_sha256':SHA((self.root/(base+'/run.py')).read_bytes()),
                                'command':'python '+base+'/run.py','environment':'Python',
                                'inputs':[{**pin,'source_path':'not-authority.js'}],'outputs':[]}}
        before=copy.deepcopy(record);path,_,_=bundle(self.root,record)
        with zipfile.ZipFile(self.root/path) as saved:
            self.assertEqual(saved.read(name),old)
            self.assertNotIn(item['path'],saved.namelist())
        self.assertEqual(record,before)
        self.assertEqual((self.root/name).read_bytes(),current)

    def test_real_dependent_validation_derives_source_path_without_rewriting_raw_record(self):
        import build_experiments as builder
        path = ROOT / 'experiments/records/prepared-opening-evidence-gates/record.json'
        before = path.read_bytes()
        pages = {row['id'] for row in json.loads((ROOT / 'data/local-run-inputs.json').read_bytes())['pages']}
        compiled = builder.validate_record(ROOT, path, pages)
        pin = next(item for item in compiled['reproduction']['inputs'] if item['path'] == NAME)
        self.assertEqual(pin['sha256'], self.item['sha256'])
        self.assertEqual(pin['source_path'], self.item['path'])
        self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
