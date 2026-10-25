"""Independent Python replay of actual browser-format family downloads, offline."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import reproduce_family as family
import research_runner as runner


class FamilyReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        code = r"""
const fs=require('node:fs'),{webcrypto}=require('node:crypto');
const F=require('./research-family.js'),E=require('./local-experiment.js'),C=require('./local-plan-controls.js');
(async()=>{const b=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8')),v=await F.snapshot(b,webcrypto),ids=F.caseIds(v),plan=await F.prepare(b,Array.from({length:12},(_,i)=>ids[i*55+i]),webcrypto),controls=[];
for(const c of plan.cases){const s=await C.prepare(c.task,webcrypto);controls.push({caseId:c.id,results:s.cases.map(f=>({id:f.id,result:E.run(f.task)}))});}
process.stdout.write(JSON.stringify({plan,results:plan.cases.map(c=>({caseId:c.id,result:E.run(c.task)})),controls}));})().catch(e=>{console.error(e);process.exitCode=1;});
"""
        generated = subprocess.run(['node', '-e', code], cwd=ROOT, check=True, capture_output=True)
        cls.batch = json.loads(generated.stdout.decode('utf-8'))

    def cli(self, source, output):
        return subprocess.run([sys.executable, str(ROOT / 'tools/reproduce_family.py'), '--batch', str(source), '--out', str(output)],
                              capture_output=True, text=True, encoding='utf-8')

    def test_full_batch_independent_replay(self):
        original = copy.deepcopy(self.batch)
        result = family.reproduce(self.batch)
        self.assertEqual(len(result['results']), 12)
        self.assertEqual(len({c['configuration'] for c in result['plan']['cases']}), 12)
        self.assertTrue(family.same(result, self.batch))
        self.assertEqual(original, self.batch)
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder) / 'download.json', Path(folder) / 'replay.json'
            source.write_text(json.dumps(self.batch, ensure_ascii=False), encoding='utf-8')
            command = self.cli(source, output)
            self.assertEqual(command.returncode, 0, command.stderr)
            self.assertIn('12 manuscript calculations', command.stdout)
            self.assertIn('Controls retained, not verified', command.stdout)
            self.assertTrue(family.same(json.loads(output.read_text(encoding='utf-8')), self.batch))
            preserved = output.read_bytes()
            self.assertNotEqual(self.cli(source, output).returncode, 0)
            self.assertEqual(output.read_bytes(), preserved)
            self.assertNotEqual(self.cli(source, source).returncode, 0)
            self.assertEqual(json.loads(source.read_text(encoding='utf-8')), self.batch)
            # The two optional downloads work together outside the repository.
            for name in ('reproduce_family.py', 'research_runner.py'):
                shutil.copyfile(ROOT / 'tools' / name, Path(folder) / name)
            detached = subprocess.run([sys.executable, 'reproduce_family.py', '--batch', source.name, '--out', 'detached.json'],
                                      cwd=folder, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(detached.returncode, 0, detached.stderr)
            self.assertTrue(family.same(json.loads((Path(folder) / 'detached.json').read_text(encoding='utf-8')), self.batch))

    def test_complete_result_and_identity_tamper(self):
        mutations = [
            lambda b: b['results'][0]['result']['metrics'].__setitem__('runes', 1),
            lambda b: b['results'][0]['result']['metrics'].__setitem__('ioc', 0.99),
            lambda b: b['results'][0]['result']['matches'][0].__setitem__('matched', 1),
            lambda b: b['results'][0]['result']['transformed'][0].__setitem__('text', 'changed'),
            lambda b: b['results'][0]['result'].__setitem__('extra', True),
            lambda b: b['results'].reverse(),
            lambda b: b['controls'].reverse(),
            lambda b: b['controls'][0]['results'][0].__setitem__('id', 'different'),
            lambda b: b['plan'].__setitem__('planId', '0' * 64),
            lambda b: b['plan']['cases'][0]['task'].__setitem__('title', 'changed'),
            lambda b: b['results'].pop(),
            lambda b: b.__setitem__('extra', True),
        ]
        for mutate in mutations:
            batch = copy.deepcopy(self.batch)
            mutate(batch)
            with self.subTest(mutate=mutate), self.assertRaises((ValueError, TypeError)):
                family.reproduce(batch)

    def test_rehashed_wrong_method_is_not_a_family_case(self):
        for field, value in [('key', [23, 12, 3, 4]), ('mode', 'repeat'), ('reset', 'word')]:
            batch = copy.deepcopy(self.batch)
            case = batch['plan']['cases'][0]
            if case['task']['steps'][0][field] == value:
                value = 'line' if field == 'reset' else 'plaintext-autokey'
            case['task']['steps'][0][field] = value
            case['task']['taskId'] = runner.task_identity(case['task'])
            batch['plan']['planId'] = hashlib.sha256(runner.canonical({k: v for k, v in batch['plan'].items() if k != 'planId'})).hexdigest()
            with self.subTest(field=field), self.assertRaises(ValueError):
                family.reproduce(batch)

    def test_strict_json_bytes_unicode_and_no_output_on_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder) / 'bad.json', Path(folder) / 'never.json'
            for raw in [b'{"plan":{},"plan":{}}', b'{"x":NaN}', b'\xff', b' ' * (family.MAX_BYTES + 1), b'{"x":"\\ud800"}']:
                source.write_bytes(raw)
                self.assertNotEqual(self.cli(source, output).returncode, 0)
                self.assertFalse(output.exists())
            bad = copy.deepcopy(self.batch)
            bad['results'][0]['result']['metrics']['ioc'] = 0.99
            source.write_text(json.dumps(bad), encoding='utf-8')
            self.assertNotEqual(self.cli(source, output).returncode, 0)
            self.assertFalse(output.exists())

    def test_float_tolerance_is_narrow_and_booleans_are_not_numbers(self):
        self.assertTrue(family.same(0.123456789 + 5e-13, 0.123456789))
        self.assertFalse(family.same(0.123456789 + 5e-10, 0.123456789))
        self.assertFalse(family.same(True, 1))
        self.assertFalse(family.same(1, True))
        self.assertFalse(family.same(float('nan'), 0.1))


if __name__ == '__main__':
    unittest.main()
