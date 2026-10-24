"""Exact numeric controls for direct word sums; no manuscript target sums."""
import copy
import json
from pathlib import Path
import subprocess
import unittest

from browser_followups import construct_word_prime_followup, compile_card, digest, runner, validate_followups

ROOT = Path(__file__).resolve().parents[1]


class WordPrimeFollowups(unittest.TestCase):
    def construct(self, **changes):
        args = dict(identifier='synthetic-word-prime-test', title='Fixed word sums',
            question='What are the exact word sums?', scope_change='One declared table and segmentation.',
            limitation='A numeric ledger is not a decryption or significance test.',
            pages=['lp2-15'], table='reversed', boundaries='hyphen-period')
        args.update(changes)
        return construct_word_prime_followup(ROOT, **args)

    def test_hand_calculated_controls_all_tables_and_boundaries_and_js_parity(self):
        for table, total, sums in [('canonical', 228, [5, 109, 114]), ('reversed', 436, [216, 2, 218])]:
            for boundaries in ('hyphen-period', 'non-rune'):
                recipe = self.construct(table=table, boundaries=boundaries)
                task = recipe['control']['task']
                result = runner.run(task)
                self.assertEqual(result['wordSums']['total'], total)
                self.assertEqual(result['wordSums']['words'], 3 if boundaries == 'hyphen-period' else 4)
                if boundaries == 'hyphen-period':
                    self.assertEqual([w['sum'] for w in result['wordSums']['pages'][0]['words']], sums)
                self.assertEqual(digest(result), recipe['control']['expected_result_sha256'])
                code = "const E=require('./local-experiment.js');let s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>process.stdout.write(JSON.stringify(E.run(JSON.parse(s)))));"
                js = subprocess.run(['node', '-e', code], input=json.dumps(task), encoding='utf-8',
                                    capture_output=True, check=True, cwd=ROOT)
                self.assertEqual(json.loads(js.stdout), result)

    def test_parameters_evaluation_and_compounds_rejected(self):
        for changes in [{'table': 'reverse-digits'}, {'boundaries': 'words'}]:
            with self.assertRaises(ValueError):
                self.construct(**changes)
        recipe = self.construct()
        for key, value in [('table', 'canonical'), ('boundaries', 'non-rune')]:
            card = copy.deepcopy(recipe['card'])
            card['rules']['evaluation']['value'][key] = value
            with self.assertRaises(ValueError):
                compile_card(card)
        card = copy.deepcopy(recipe['card'])
        card['method']['value']['operations'].append({'id': 'affine', 'a': 28, 'b': 28})
        with self.assertRaises(ValueError):
            compile_card(card)

    def test_controls_and_pins_must_still_match_exactly(self):
        for part in ('criterion', 'digest', 'pin', 'reset'):
            recipe = self.construct()
            if part == 'criterion':
                recipe['control']['task']['criterion']['table'] = 'canonical'
                recipe['control']['task']['taskId'] = runner.task_identity(recipe['control']['task'])
            elif part == 'digest':
                recipe['control']['expected_result_sha256'] = '0' * 64
            elif part == 'reset':
                recipe['card']['rules']['reset'] = {'status': 'specified', 'value': 'word'}
            else:
                recipe['inputs']['pages'][0]['text_sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                validate_followups([recipe], ROOT)

    def test_authoring_never_runs_target(self):
        original = runner.run
        tasks = []
        def synthetic_only(task):
            self.assertIn('Synthetic', task['title'])
            self.assertEqual([p['id'] for p in task['pages']], ['lp1-01'])
            tasks.append(task)
            return original(task)
        try:
            runner.run = synthetic_only
            self.construct(pages=[f'lp2-{n:02d}' for n in range(56)])
        finally:
            runner.run = original
        self.assertGreaterEqual(len(tasks), 2)


if __name__ == '__main__':
    unittest.main()
