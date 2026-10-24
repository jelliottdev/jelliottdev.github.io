"""Literal interruption authoring is a partial encoder, never a bijection."""
import copy
import unittest
from pathlib import Path

from browser_followups import (alphabet, compile_card, construct_followup, construct_measurement_followup,
                               digest, inverse_step, runner, validate_followups, warning_plaintext)

ROOT = Path(__file__).resolve().parents[1]


class InterruptedFollowups(unittest.TestCase):
    def operation(self, **changes):
        op = {'id': 'interrupted_repeating_key', 'label': 'Interrupted repeating key',
              'key': [0], 'direction': 'subtract', 'reset': 'word', 'interrupts': [0]}
        op.update(changes)
        return op

    def construct(self, op):
        return construct_followup(ROOT, identifier='synthetic-interrupted-test',
            title='Synthetic interrupted-key test', question='Does the fixed Warning prefix match?',
            scope_change='One explicit literal input interruption rule.',
            limitation='This synthetic authoring fixture makes no manuscript claim.',
            operations=[op], pages=['lp2-15'])

    def test_partial_encoder_hand_vectors_and_exact_clocks(self):
        ordered = alphabet(ROOT)
        runes = [x['rune'] for x in ordered]
        text = lambda values: ''.join(runes[n] for n in values)
        for direction, expected in [('subtract', [4, 0, 6, 4]), ('add', [2, 0, 2, 2])]:
            step = {'op': 'interrupted-keyed-shift', 'key': [1, 2],
                    'direction': direction, 'reset': 'word', 'interrupts': [0]}
            plain = text([3, 0, 4, 3])
            self.assertEqual(inverse_step(plain, step, ordered), text(expected))
            for reset, separator in [('word', '-'), ('word', '\t'), ('line', '\r\n')]:
                step['reset'] = reset
                self.assertEqual(inverse_step(plain + separator + plain, step, ordered),
                                 text(expected) + separator + text(expected))

    def test_rejects_unrepresentable_plaintext_without_rewriting(self):
        ordered = alphabet(ROOT)
        runes = [x['rune'] for x in ordered]
        for direction, value in [('subtract', 28), ('add', 1)]:
            step = {'op': 'interrupted-keyed-shift', 'key': [1], 'direction': direction,
                    'reset': 'page', 'interrupts': [0]}
            with self.assertRaisesRegex(ValueError, 'cannot be encoded'):
                inverse_step(runes[value], step, ordered)
        # Literal interruption is explicitly chosen even where another input
        # could decode to zero. This documents ambiguity rather than hiding it.
        step['direction'] = 'subtract'
        self.assertEqual(inverse_step(runes[0], step, ordered), runes[0])

    def test_constructor_preserves_full_warning_and_explicit_program(self):
        recipe = self.construct(self.operation())
        plan = compile_card(recipe['card'])
        self.assertEqual(plan['steps'], [{'op': 'interrupted-keyed-shift', 'key': [0],
            'direction': 'subtract', 'reset': 'word', 'interrupts': [0]}])
        plain, _ = warning_plaintext(ROOT, alphabet(ROOT))
        self.assertEqual(runner.run(recipe['control']['task'])['transformed'][0]['text'], plain)

    def test_rejects_incomplete_ambiguous_or_conflicting_cards(self):
        for changes in [{'key': []}, {'key': [0] * 257}, {'key': [True]}, {'interrupts': []},
                        {'interrupts': [1, 0]}, {'interrupts': [0, 0]}, {'interrupts': [29]},
                        {'interrupts': [False]}, {'reset': 'none'}, {'direction': 'infer'}]:
            with self.assertRaises(ValueError):
                self.construct(self.operation(**changes))
        card = self.construct(self.operation())['card']
        altered = copy.deepcopy(card)
        altered['rules']['reset']['value'] = 'page'
        with self.assertRaises(ValueError):
            compile_card(altered)

    def measurement(self):
        runes = [row['rune'] for row in alphabet(ROOT)]
        # Hand-calculated key23,12,4; F copies and holds. Restart at '-'.
        cipher = ''.join(runes[n] for n in [7, 0, 4, 0, 19, 0, 2, 8, 0])
        plain = ''.join(runes[n] for n in [13, 0, 21, 0, 15, 0, 8, 25, 0])
        return construct_measurement_followup(ROOT, identifier='synthetic-interrupted-measurement',
            title='Descriptive literal-F control', question='What does this exact rule output?',
            scope_change='Restart at word boundaries.', limitation='Descriptive metrics are not a reading.',
            operations=[self.operation(key=[23, 12, 4])], pages=['lp2-11'],
            control_cipher=cipher + '-' + cipher, control_plain=plain + '-' + plain)

    def test_measurement_has_complete_independently_expected_control(self):
        recipe = self.measurement()
        self.assertEqual(compile_card(recipe['card'])['criterion'], {'kind': 'measurement'})
        task = recipe['control']['task']
        result = runner.run(task)
        self.assertTrue(all(row['matched'] for row in result['matches']))
        self.assertEqual(len(task['criterion']['values']), 18)
        for mutation in ('interrupts', 'reset'):
            wrong = copy.deepcopy(task)
            if mutation == 'interrupts':
                wrong['steps'][0]['interrupts'] = [28]
            else:
                wrong['steps'][0]['reset'] = 'page'
            wrong['taskId'] = runner.task_identity(wrong)
            self.assertFalse(runner.run(wrong)['matches'][0]['matched'])

    def test_measurement_rejects_no_exact_gate_or_incomplete_witness(self):
        recipe = self.measurement()
        for change in ('measurement', 'short', 'wrong-program'):
            altered = copy.deepcopy(recipe)
            task = altered['control']['task']
            if change == 'measurement':
                task['criterion'] = {'kind': 'measurement'}
            elif change == 'short':
                task['criterion']['values'] = task['criterion']['values'][:12]
            else:
                task['steps'][0]['key'] = [0]
            task['taskId'] = runner.task_identity(task)
            altered['control']['expected_result_sha256'] = digest(runner.run(task))
            with self.assertRaises(ValueError):
                validate_followups([altered], ROOT)


if __name__ == '__main__':
    unittest.main()
