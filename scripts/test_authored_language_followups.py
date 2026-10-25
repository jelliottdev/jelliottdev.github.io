"""Authored language comparisons pin one evaluator and verify complete controls.

Only the independently specified synthetic witness is executed. Manuscript text
is read solely for source hash pins; a planted plaintext never defines a score
threshold or supplies evidence for the target hypothesis.
"""
import copy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import browser_followups as authored

ROOT = Path(__file__).resolve().parents[1]
CRITERION = {
    'kind': 'language-score', 'modelId': 'gp29-flores-trigram-v1',
    'modelSha256': '8a5171ba8bfc5bea73e7ce7a38bca85cd99bc2175535a27e21450208dbdbaad4',
}


class AuthoredLanguageFollowups(unittest.TestCase):
    def construct(self, **changes):
        alphabet = authored.alphabet(ROOT)
        runes = [row['rune'] for row in alphabet]
        # Hand-derived: subtract [1, 2] restarted at each word. Third rune
        # wraps to the first key element. Includes line and punctuation resets.
        inputs = [1, 4, 7]
        outputs = [0, 2, 6]
        cipher = '-'.join(''.join(runes[n] for n in inputs) for _ in range(17))
        plain = '-'.join(''.join(runes[n] for n in outputs) for _ in range(17))
        values = dict(identifier='synthetic-language-followup',
                      title='Compare a fixed word-reset output with language samples',
                      question='Does this one fixed output resemble the reference samples?',
                      scope_change='One fixed transformation on one source page.',
                      limitation='A score is not a reading or language identification.',
                      operations=[{'id': 'repeating_key', 'key': [1, 2],
                                   'direction': 'subtract', 'reset': 'word'}],
                      pages=['lp2-15'], control_cipher=cipher, control_plain=plain)
        values.update(changes)
        actual_run = authored.runner.run
        seen = []

        def only_synthetic(task):
            self.assertEqual(task['criterion']['kind'], 'exact-prefix')
            self.assertEqual(task['pages'], [{'id': 'lp1-01', 'text': values['control_cipher']}])
            seen.append(copy.deepcopy(task))
            return actual_run(task)

        with patch.object(authored.runner, 'run', only_synthetic):
            recipe = authored.construct_language_followup(ROOT, **values)
        self.assertTrue(seen)
        return recipe

    def validate(self, recipe):
        return authored.validate_followups([recipe], ROOT)

    def test_maintained_pins_and_complete_hand_derived_control(self):
        recipe = self.construct()
        before = copy.deepcopy(recipe)
        plan = authored.compile_card(recipe['card'])
        self.assertEqual(plan['criterion'], CRITERION)
        self.assertEqual(authored.LANGUAGE_CRITERION, CRITERION)
        task = recipe['control']['task']
        self.assertEqual(task['steps'], plan['steps'])
        self.assertEqual(task['criterion']['values'], [0, 2, 6] * 17)
        result = authored.runner.run(task)
        self.assertEqual([m['matched'] for m in result['matches']], [True])
        self.assertEqual(recipe['control']['expected_result_sha256'], authored.digest(result))
        self.assertEqual(self.validate(recipe), [before])
        self.assertEqual(recipe, before)
        self.assertNotIn('languageScore', result)

    def test_no_arbitrary_model_or_threshold_is_admitted(self):
        mutations = [dict(CRITERION, modelId='another-model'),
                     dict(CRITERION, modelSha256='0' * 64),
                     dict(CRITERION, threshold=0),
                     dict(CRITERION, kind='language'),
                     {k: v for k, v in CRITERION.items() if k != 'modelSha256'}]
        for criterion in mutations:
            with self.subTest(criterion=criterion):
                recipe = self.construct()
                recipe['card']['rules']['evaluation']['value'] = criterion
                with self.assertRaises(ValueError):
                    self.validate(recipe)

    def test_prefix_only_scored_and_changed_program_controls_are_rejected(self):
        original = self.construct()
        for change in ('short-prefix', 'score-control', 'program', 'digest', 'wrong-last-rune'):
            with self.subTest(change=change):
                recipe = copy.deepcopy(original)
                task = recipe['control']['task']
                if change == 'short-prefix':
                    task['criterion']['values'] = task['criterion']['values'][:12]
                elif change == 'score-control':
                    task['criterion'] = copy.deepcopy(CRITERION)
                elif change == 'program':
                    task['steps'][0]['reset'] = 'page'
                elif change == 'wrong-last-rune':
                    task['criterion']['values'][-1] = 7
                else:
                    recipe['control']['expected_result_sha256'] = '0' * 64
                task['taskId'] = authored.runner.task_identity(task)
                with self.assertRaises(ValueError):
                    self.validate(recipe)

    def test_input_pins_and_scope_order_cannot_drift(self):
        original = self.construct(pages=['lp2-16', 'lp2-15'])
        self.assertEqual(authored.compile_card(original['card'])['pages'], ['lp2-15', 'lp2-16'])
        for change in ('alphabet', 'text', 'version', 'order', 'extra-page'):
            with self.subTest(change=change):
                recipe = copy.deepcopy(original)
                if change == 'alphabet':
                    recipe['inputs']['alphabet_sha256'] = '0' * 64
                elif change == 'text':
                    recipe['inputs']['pages'][0]['text_sha256'] = '0' * 64
                elif change == 'version':
                    recipe['inputs']['version'] = 'reviewed'
                elif change == 'order':
                    recipe['inputs']['pages'].reverse()
                else:
                    recipe['card']['scope']['value']['pages'].append('lp2-17')
                with self.assertRaises(ValueError):
                    self.validate(recipe)

    def test_control_needs_exact_independent_output_and_separators(self):
        runes = [row['rune'] for row in authored.alphabet(ROOT)]
        for cipher, plain in [(runes[1], runes[1]),
                              (runes[1] + '-', runes[0] + '.'),
                              ('-', '-')]:
            with self.subTest(cipher=cipher, plain=plain):
                with self.assertRaises(ValueError):
                    self.construct(control_cipher=cipher, control_plain=plain)

    def test_production_js_compiler_and_complete_synthetic_result_parity(self):
        recipe = self.construct()
        script = r'''
import fs from 'node:fs';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
import L from './local-experiment.js';import {validateCard} from './services/idea-assistant/idea-relations.mjs';
import {planCard} from './services/idea-assistant/prepare-task.mjs';
const recipe=JSON.parse(fs.readFileSync(0,'utf8'));
assert.deepEqual(validateCard(recipe.card),recipe.card);
const plan=planCard(recipe.card);assert(!plan.reason,plan.reason);
assert.deepEqual(plan.steps,recipe.control.task.steps);
assert.deepEqual(plan.criterion,recipe.card.rules.evaluation.value);
await L.checkIdentity(recipe.control.task);
const result=L.run(recipe.control.task);assert(result.matches.every(row=>row.matched));
assert.equal(createHash('sha256').update(L.stable(result)).digest('hex'),recipe.control.expected_result_sha256);
assert(!Object.hasOwn(result,'languageScore'));
process.stdout.write(JSON.stringify({criterion:plan.criterion,result}));
'''
        completed = subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT,
                                   input=json.dumps(recipe, ensure_ascii=False), capture_output=True,
                                   text=True, encoding='utf-8', check=True)
        js = json.loads(completed.stdout)
        self.assertEqual(js['criterion'], CRITERION)
        self.assertEqual(js['result'], authored.runner.run(recipe['control']['task']))


if __name__ == '__main__':
    unittest.main()
