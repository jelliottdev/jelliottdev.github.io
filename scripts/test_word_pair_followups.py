"""Authored fixed-count controls; no manuscript relation counts are executed."""
import copy
import json
from pathlib import Path
import subprocess
import unittest

from browser_followups import construct_word_pair_followup, compile_card, digest, runner, validate_followups

ROOT = Path(__file__).resolve().parents[1]


class WordPairFollowups(unittest.TestCase):
    def construct(self, **changes):
        args = dict(identifier='synthetic-pair-test', title='Fixed pair measurement',
                    question='Does this exact pair relation occur?',
                    scope_change='Compare one explicitly specified boundary rule.',
                    limitation='This fixed count does not identify a cipher or establish significance.',
                    pages=['lp2-00'], lag=6, a=27, b=24, boundaries='non-rune')
        args.update(changes)
        return construct_word_pair_followup(ROOT, **args)

    def test_complete_synthetic_control_and_javascript_parity(self):
        for boundaries in ('non-rune', 'hyphen-period'):
            recipe = self.construct(boundaries=boundaries)
            task = recipe['control']['task']
            result = runner.run(task)
            self.assertEqual(task['steps'], [])
            self.assertEqual(result['wordPairs']['opportunities'], 20)
            self.assertEqual(result['wordPairs']['matches'], 20)
            alternate = copy.deepcopy(task)
            alternate['criterion']['boundaries'] = 'hyphen-period' if boundaries == 'non-rune' else 'non-rune'
            alternate['taskId'] = runner.task_identity(alternate)
            changed = runner.run(alternate)
            self.assertNotEqual(changed['wordPairs'], result['wordPairs'])
            self.assertNotEqual(changed['wordPairs']['opportunities'], 20)
            self.assertEqual(digest(result), recipe['control']['expected_result_sha256'])
            code = "const E=require('./local-experiment.js');let s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>process.stdout.write(JSON.stringify(E.run(JSON.parse(s)))));"
            js = subprocess.run(['node', '-e', code], input=json.dumps(task), text=True, encoding='utf-8',
                                capture_output=True, check=True, cwd=ROOT)
            self.assertEqual(json.loads(js.stdout), result)

    def test_evaluation_and_method_must_match(self):
        recipe = self.construct()
        for key, value in [('lag', 5), ('a', 2), ('b', 0), ('boundaries', 'hyphen-period')]:
            card = copy.deepcopy(recipe['card'])
            card['rules']['evaluation']['value'][key] = value
            with self.assertRaises(ValueError):
                compile_card(card)

    def test_rejects_transforms_and_irrelevant_rules(self):
        recipe = self.construct()
        for name, value in [('reset', 'word'), ('initialState', 0), ('boundaryMode', 'within_words'),
                            ('wordBoundaries', 'ignore')]:
            card = copy.deepcopy(recipe['card'])
            card['rules'][name] = {'status': 'specified', 'value': value}
            with self.assertRaises(ValueError):
                compile_card(card)
        card = copy.deepcopy(recipe['card'])
        card['method']['value']['operations'].append({'id': 'affine', 'a': 1, 'b': 0})
        with self.assertRaises(ValueError):
            compile_card(card)

    def test_explicit_parameters_and_detectable_control(self):
        for changes in [dict(lag=True), dict(lag=0), dict(lag=13), dict(a=29), dict(b=False),
                        dict(boundaries='spaces'), dict(lag=1, a=1, b=0)]:
            with self.assertRaises(ValueError):
                self.construct(**changes)

    def test_control_digest_and_source_pins_are_mandatory(self):
        for part in ('control', 'inputs'):
            recipe = self.construct()
            if part == 'control':
                recipe[part]['expected_result_sha256'] = '0' * 64
            else:
                recipe[part]['pages'][0]['text_sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                validate_followups([recipe], ROOT)

    def test_target_execution_is_not_part_of_authoring(self):
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
