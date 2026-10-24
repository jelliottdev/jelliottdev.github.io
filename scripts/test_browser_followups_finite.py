"""Finite-stream authoring controls; no manuscript target transformations."""
import copy
import json
from pathlib import Path
import re
import subprocess
import unittest

from browser_followups import (alphabet, compile_card, construct_followup,
                               inverse_step, runner, warning_plaintext)

ROOT = Path(__file__).resolve().parents[1]


class FiniteFollowups(unittest.TestCase):
    def construct(self, operations, pages=None):
        return construct_followup(ROOT, identifier='synthetic-finite-test',
            title='Synthetic finite-stream test', question='Does the fixed Warning prefix match?',
            scope_change='One exact finite stream, without repetitions or feedback.',
            limitation='This test fixture does not claim a manuscript result.',
            operations=operations, pages=pages or ['lp2-15'])

    def operation(self, *, key=None, direction='subtract', reset='page'):
        return {'id': 'finite_key', 'label': 'Finite key stream',
                'key': [n % 29 for n in range(184)] if key is None else key,
                'direction': direction, 'reset': reset}

    def test_inverse_hand_vectors_and_separators(self):
        a = alphabet(ROOT)
        runes = [row['rune'] for row in a]
        plain = ''.join(runes[n] for n in [0, 0, 2, 2])
        key = [1, 2, 3, 4]
        for direction, expected in [('subtract', [1, 2, 5, 6]), ('add', [28, 27, 28, 27])]:
            step = {'op': 'finite-shift', 'key': key, 'direction': direction, 'reset': 'page'}
            encoded = ''.join(runes[n] for n in expected)
            self.assertEqual(inverse_step(plain, step, a), encoded)
            for reset, separator in [('word', '-'), ('word', '\t'), ('line', '\r\n')]:
                step['reset'] = reset
                self.assertEqual(inverse_step(plain + separator + plain, step, a), encoded + separator + encoded)
        # Finite streams do not silently cycle after the last element.
        with self.assertRaisesRegex(ValueError, 'finite key exhausted'):
            inverse_step(plain + runes[1], step | {'reset': 'page'}, a)

    def test_full_warning_inverse_control_and_compiler_js_parity(self):
        families = [[self.operation(direction=direction, reset=reset)]
                    for direction in ('subtract', 'add') for reset in ('page', 'line', 'word')]
        families.append([{'id': 'reverse_runes', 'label': 'Reverse rune order within each word', 'unit': 'word'},
                         self.operation(direction='add', reset='line'),
                         {'id': 'cumulative_difference', 'reset': 'word'}])
        recipes = []
        plain, _ = warning_plaintext(ROOT, alphabet(ROOT))
        for operations in families:
            before = copy.deepcopy(operations)
            recipe = self.construct(operations)
            self.assertEqual(operations, before)
            self.assertEqual(runner.run(recipe['control']['task'])['transformed'][0]['text'], plain)
            self.assertEqual(compile_card(recipe['card'])['steps'], recipe['control']['task']['steps'])
            recipes.append(recipe)
        script = r'''
import fs from 'node:fs';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
import L from './local-experiment.js';import {validateCard} from './services/idea-assistant/idea-relations.mjs';
import {planCard} from './services/idea-assistant/prepare-task.mjs';
for(const recipe of JSON.parse(fs.readFileSync(0,'utf8'))){
 assert.deepEqual(validateCard(recipe.card),recipe.card);
 const plan=planCard(recipe.card);assert(!plan.reason,plan.reason);
 assert.deepEqual(plan.steps,recipe.control.task.steps);
 await L.checkIdentity(recipe.control.task);
 const result=L.run(recipe.control.task);assert(result.matches.every(m=>m.matched));
 assert.equal(createHash('sha256').update(L.stable(result)).digest('hex'),recipe.control.expected_result_sha256);
}process.stdout.write('finite authoring JS/Python parity passed');
'''
        completed = subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT,
            input=json.dumps(recipes, ensure_ascii=False), capture_output=True,
            text=True, encoding='utf-8')
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('parity passed', completed.stdout)

    def test_exact_exhaustion_boundaries_and_no_short_prefix_escape(self):
        # A 12-rune acceptance rule must still recover the complete 184-rune control.
        with self.assertRaises(ValueError):
            self.construct([self.operation(key=[1] * 12)])
        self.construct([self.operation(key=[1] * 184)])
        # Enough for the 184-rune control is not enough for a longer target.
        with self.assertRaises(ValueError):
            self.construct([self.operation(key=[1] * 184)], pages=['lp2-00'])
        self.construct([self.operation(key=[1] * 262)], pages=['lp2-00'])
        plain, _ = warning_plaintext(ROOT, alphabet(ROOT))
        runes = {row['rune'] for row in alphabet(ROOT)}
        longest = max(map(len, re.findall('[' + ''.join(runes) + ']+', plain)))
        self.construct([self.operation(key=[1] * longest, reset='word')])
        with self.assertRaises(ValueError):
            self.construct([self.operation(key=[1] * (longest - 1), reset='word')])

    def test_invalid_values_wording_and_unknown_rules_are_not_repaired(self):
        for key in ([], [True], [29], [-1], [1] * 20001):
            with self.assertRaises(ValueError):
                self.construct([self.operation(key=key)])
        for field, value in [('direction', 'either'), ('reset', 'none'), ('label', 'Prime stream'), ('skip', 1)]:
            operation = self.operation()
            operation[field] = value
            with self.assertRaises(ValueError):
                self.construct([operation])


if __name__ == '__main__':
    unittest.main()
