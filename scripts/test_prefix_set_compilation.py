"""Opening-set compile parity and exact full-output synthetic controls; no target runs."""
import copy
import json
from pathlib import Path
import subprocess
import unittest
import browser_followups as fixed

ROOT = Path(__file__).resolve().parents[1]
SET = {'kind': 'exact-prefix-set', 'openings': [{'id': 'first', 'values': [0]}, {'id': 'second', 'values': [0, 1]}]}

class OpeningSetCompilation(unittest.TestCase):
    def base(self):
        recipe = json.loads((ROOT / 'experiments/records/lp2-known-vigenere-keys/record.json').read_text(encoding='utf-8'))['browser_followups'][0]
        recipe['card']['rules']['evaluation']['value'] = copy.deepcopy(SET)
        return recipe

    def test_independent_compiler_preserves_order_and_rejects_malformed_sets(self):
        r = self.base()
        self.assertEqual(fixed.compile_card(r['card'])['criterion'], SET)
        source = "const fs=require('fs'),C=require('./fixed-plan-compiler.js');console.log(JSON.stringify(C.compile(JSON.parse(fs.readFileSync(0,'utf8')))));"
        browser = json.loads(subprocess.check_output(['node', '-e', source], input=json.dumps(r['card']), cwd=ROOT, encoding='utf-8'))
        self.assertEqual(browser['criterion'], SET)
        for value in [[], [{'id': 'A', 'values': [0]}], [{'id': 'first', 'values': [True]}], [{'id': 'first', 'values': [29]}], [{'id': 'first', 'values': []}], [{'id': 'first', 'values': [0]}, {'id': 'second', 'values': [0]}], [{'id': 'first', 'values': [0]}, {'id': 'first', 'values': [1]}]]:
            bad = self.base()
            bad['card']['rules']['evaluation']['value']['openings'] = value
            with self.assertRaises(ValueError):
                fixed.compile_card(bad['card'])

    def test_set_target_requires_exact_complete_synthetic_output_not_short_acceptance_prefix(self):
        r = self.base()
        with self.assertRaisesRegex(ValueError, 'every synthetic output rune'):
            fixed.validate_followups([r], ROOT)
        task = r['control']['task']
        old = fixed.runner.run(task)
        indices = {row['rune']: n for n, row in enumerate(task['alphabet'])}
        task['criterion']['values'] = [indices[ch] for ch in old['transformed'][0]['text'] if ch in indices]
        task['taskId'] = fixed.runner.task_identity(task)
        r['control']['expected_result_sha256'] = fixed.digest(fixed.runner.run(task))
        self.assertEqual(fixed.validate_followups([r], ROOT), [r])
        broken = copy.deepcopy(r)
        broken['control']['task']['criterion'] = copy.deepcopy(SET)
        broken['control']['task']['taskId'] = fixed.runner.task_identity(broken['control']['task'])
        with self.assertRaisesRegex(ValueError, 'exact synthetic control'):
            fixed.validate_followups([broken], ROOT)

if __name__ == '__main__':
    unittest.main()
