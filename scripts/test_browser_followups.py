"""Authored recipe validation; only synthetic data is transformed, never targets."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from browser_followups import (KEY, WARNING12, alphabet, compile_card,
                               construct_second_koan_word_reset, construct_followup, digest,
                               inverse_step, warning_plaintext, text_hash, validate_followups, runner)

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / 'experiments/records/lp2-known-vigenere-keys/record.json'


class BrowserFollowups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(RECORD.read_text(encoding='utf-8'))['browser_followups'][0]

    def validate(self, recipe):
        return validate_followups([recipe], ROOT)

    def changed(self):
        return copy.deepcopy(self.recipe)

    def test_optional_motivation_is_editorial_and_plain_unicode(self):
        legacy = self.changed()
        legacy.pop('motivation', None)
        self.assertEqual(self.validate(legacy), [legacy])
        before = copy.deepcopy(legacy)
        for motivation in ('Explain why this exact comparison is useful.', '\U0001f9e9' * 500):
            recipe = copy.deepcopy(legacy)
            recipe['motivation'] = motivation
            self.assertEqual(self.validate(recipe), [recipe])
            self.assertEqual(recipe['motivation'], motivation)
            self.assertEqual(compile_card(recipe['card']), compile_card(legacy['card']))
            self.assertEqual(recipe['control'], legacy['control'])
            self.assertNotEqual(digest(recipe), digest(legacy))
        self.assertEqual(legacy, before)
        invalid = (None, False, 1, [], {}, '', ' ', ' padded', 'padded ', 'x' * 501,
                   '\U0001f9e9' * 501, '<b>why</b>', '[link](url)', '`code`', '*bold*',
                   'one\ntwo', 'one\rtwo', 'one\ttwo', 'one\x00two', 'one\x7ftwo',
                   'one\x85two', 'one\u2028two', 'one\u2029two', '\ud800')
        for motivation in invalid:
            recipe = copy.deepcopy(legacy)
            recipe['motivation'] = motivation
            with self.assertRaisesRegex(ValueError, 'motivation'):
                self.validate(recipe)

    def construct(self, operations, **extra):
        return construct_followup(ROOT, identifier='synthetic-constructor-test',
                                  title='Synthetic constructor test', question='Does the fixed Warning beginning match?',
                                  scope_change='One explicitly declared synthetic-control test variant.',
                                  limitation='A matching prefix is not a complete decipherment.',
                                  operations=operations, pages=['lp2-15'], **extra)

    def test_independent_autokey_inverse_hand_vectors(self):
        a = alphabet(ROOT)
        runes = [entry['rune'] for entry in a]
        ciphertext = ''.join(runes[n] for n in [1, 2, 3, 4, 5, 6])
        vectors = {
            ('repeat', 'subtract'): [0, 0, 2, 2, 4, 4],
            ('plaintext-autokey', 'subtract'): [0, 0, 3, 4, 2, 2],
            ('ciphertext-autokey', 'subtract'): [0, 0, 2, 2, 2, 2],
            ('repeat', 'add'): [2, 4, 4, 6, 6, 8],
            ('plaintext-autokey', 'add'): [2, 4, 5, 8, 10, 14],
            ('ciphertext-autokey', 'add'): [2, 4, 4, 6, 8, 10],
        }
        for (mode, direction), values in vectors.items():
            step = {'op': 'keyed-shift', 'key': [1, 2], 'mode': mode, 'direction': direction, 'reset': 'page'}
            plaintext = ''.join(runes[n] for n in values)
            self.assertEqual(inverse_step(plaintext, step, a), ciphertext, (mode, direction))
            # Non-rune separators reset word clocks and CR/LF reset line clocks.
            for reset, separator in [('word', '-'), ('word', '\t'), ('line', '\r\n')]:
                step['reset'] = reset
                self.assertEqual(inverse_step(plaintext + separator + plaintext, step, a),
                                 ciphertext + separator + ciphertext, (mode, direction, reset))

    def test_ordered_multistep_inversion_and_full_plaintext_not_only_prefix(self):
        a = alphabet(ROOT)
        plain, _ = warning_plaintext(ROOT, a)
        operations = [{'id': 'affine', 'a': 7, 'b': 7},
                      {'id': 'plaintext_autokey', 'key': [1, 2], 'direction': 'subtract', 'reset': 'page'},
                      {'id': 'reverse_runes', 'label': 'Reverse rune order within each word', 'unit': 'word'}]
        before = copy.deepcopy(operations)
        recipe = self.construct(operations)
        self.assertEqual(operations, before)
        task = recipe['control']['task']
        self.assertEqual(runner.run(task)['transformed'][0]['text'], plain)
        correct = plain
        for step in reversed(task['steps']):
            correct = inverse_step(correct, step, a)
        self.assertEqual(task['pages'][0]['text'], correct)
        wrong_order = plain
        for step in task['steps']:
            wrong_order = inverse_step(wrong_order, step, a)
        self.assertNotEqual(wrong_order, correct, 'This fixture must detect an incorrect inverse operation order')
        mutated = copy.deepcopy(task)
        mutated['pages'][0]['text'] = wrong_order
        mutated['taskId'] = runner.task_identity(mutated)
        self.assertNotEqual(runner.run(mutated)['transformed'][0]['text'], plain)

    def test_mixed_resets_longer_prefix_and_reviewed_pins(self):
        _, values = warning_plaintext(ROOT, alphabet(ROOT))
        operations = [{'id': 'cumulative_difference', 'reset': 'line'},
                      {'id': 'ciphertext_autokey', 'key': KEY[:], 'direction': 'add', 'reset': 'page'}]
        recipe = self.construct(operations, prefix=values[:64], input_version='reviewed')
        self.assertEqual(recipe['card']['rules']['reset'], {'status': 'unspecified'})
        self.assertEqual(recipe['card']['rules']['initialState'], {'status': 'specified', 'value': 0})
        self.assertEqual(recipe['control']['task']['criterion']['values'], values[:64])
        source = json.loads((ROOT / 'data/pages/lp2-15.json').read_text(encoding='utf-8'))
        self.assertEqual(recipe['inputs']['pages'][0]['text_sha256'], text_hash(source['reviewed_text']))
        self.assertEqual(recipe['inputs']['version'], 'reviewed')

    def test_generic_constructor_fails_closed_without_rescuing_parameters(self):
        bad = [[], [{'id': 'affine', 'a': 0, 'b': 7}], [{'id': 'affine', 'a': True, 'b': 7}],
               [{'id': 'reverse_runes', 'unit': 'word'}], [{'id': 'unknown'}],
               [{'id': 'repeating_key', 'key': [1], 'direction': 'subtract'}],
               [{'id': 'plaintext_autokey', 'key': [True], 'direction': 'add', 'reset': 'page'}],
               [{'id': 'ciphertext_autokey', 'key': [1], 'direction': 'add', 'reset': 'page', 'skip': 1}]]
        for operations in bad:
            with self.assertRaises(ValueError, msg=str(operations)):
                self.construct(operations)
        for prefix in ([0], [], WARNING12 + [True]):
            with self.assertRaisesRegex(ValueError, 'prefix'):
                self.construct([{'id': 'affine', 'a': 28, 'b': 28}], prefix=prefix)
        with self.assertRaises(ValueError):
            self.construct([{'id': 'affine', 'a': 1, 'b': 0}], input_version='other')

    def test_all_supported_inverse_controls_match_full_production_js_results(self):
        families = []
        for unit in ('line', 'word', 'page'):
            families.append([{'id': 'reverse_runes', 'label': 'Reverse rune order within each ' + unit, 'unit': unit}])
            families.append([{'id': 'cumulative_difference', 'label': 'Cumulative difference', 'reset': unit}])
        for a, b in [(1, 0), (7, 7), (28, 28)]:
            families.append([{'id': 'affine', 'label': 'Affine substitution', 'a': a, 'b': b}])
        for mode in ('repeating_key', 'plaintext_autokey', 'ciphertext_autokey'):
            for direction in ('subtract', 'add'):
                for reset in ('page', 'line', 'word'):
                    families.append([{'id': mode, 'key': [1, 2], 'direction': direction, 'reset': reset}])
        families.extend([
            [{'id': 'reverse_row_runes', 'label': 'Reverse rune order within rows'}],
            [{'id': 'affine', 'a': 7, 'b': 7}, {'id': 'cumulative_difference', 'reset': 'word'},
             {'id': 'repeating_key', 'key': KEY[:], 'direction': 'subtract', 'reset': 'line'}],
            [{'id': 'ciphertext_autokey', 'key': [28], 'direction': 'add', 'reset': 'page'},
             {'id': 'reverse_runes', 'label': 'Reverse rune order within each page', 'unit': 'page'},
             {'id': 'plaintext_autokey', 'key': [7, 1, 0], 'direction': 'subtract', 'reset': 'word'}],
        ])
        recipes = [self.construct(operations) for operations in families]
        script = r'''
import fs from 'node:fs';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
import L from './local-experiment.js';import {validateCard} from './services/idea-assistant/idea-relations.mjs';
import {planCard} from './services/idea-assistant/prepare-task.mjs';
const recipes=JSON.parse(fs.readFileSync(0,'utf8')),raw=JSON.parse(fs.readFileSync('data/pages/lp1-01.json','utf8')).raw;
for(const f of recipes){assert.deepEqual(validateCard(f.card),f.card);const plan=planCard(f.card);assert(!plan.reason,plan.reason);
 assert.deepEqual(plan.steps,f.control.task.steps);assert.deepEqual(plan.criterion,f.control.task.criterion);
 await L.checkIdentity(f.control.task);const result=L.run(f.control.task),runes=f.control.task.alphabet.map(r=>r.rune);
 const known=Array.from(raw,ch=>runes.includes(ch)?runes[28-runes.indexOf(ch)]:ch).join('');
 assert.equal(result.transformed[0].text,known);assert(result.matches.every(m=>m.matched));
 assert.equal(createHash('sha256').update(L.stable(result)).digest('hex'),f.control.expected_result_sha256);
}process.stdout.write(JSON.stringify({count:recipes.length}));
'''
        completed = subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT,
                                   input=json.dumps(recipes, ensure_ascii=False), capture_output=True,
                                   text=True, encoding='utf-8', check=True)
        self.assertEqual(json.loads(completed.stdout)['count'], len(families))

    def test_constructor_reproduces_exact_authored_recipe_without_targets(self):
        numerical_recipe = self.changed()
        numerical_recipe.pop('motivation', None)
        self.assertEqual(construct_second_koan_word_reset(ROOT), numerical_recipe)
        before = copy.deepcopy(self.recipe)
        self.assertEqual(self.validate(self.recipe), [before])
        self.assertEqual(self.recipe, before)

    def test_full_warning_control_and_separators(self):
        task = self.recipe['control']['task']
        result = runner.run(task)
        a = alphabet(ROOT)
        indices = {row['rune']: n for n, row in enumerate(a)}
        runes = list(indices)
        raw = json.loads((ROOT / 'data/pages/lp1-01.json').read_text(encoding='utf-8'))['raw']
        expected = ''.join(runes[28 - indices[ch]] if ch in indices else ch for ch in raw)
        self.assertEqual(result['transformed'], [{'page': 'lp1-01', 'text': expected}])
        self.assertEqual(result['metrics']['runes'], 184)
        self.assertEqual([indices[c] for c in expected if c in indices][:12], WARNING12)
        self.assertEqual([(i, c) for i, c in enumerate(task['pages'][0]['text']) if c not in indices],
                         [(i, c) for i, c in enumerate(raw) if c not in indices])
        self.assertEqual(digest(result), self.recipe['control']['expected_result_sha256'])

    def test_exact_complete_target_pins_not_original_grid(self):
        recipe = self.recipe
        expected = ['lp2-54']
        self.assertEqual([p['id'] for p in recipe['inputs']['pages']], expected)
        plan = compile_card(recipe['card'])
        self.assertEqual(plan['pages'], expected)
        self.assertEqual(plan['criterion'], {'kind': 'exact-prefix', 'values': WARNING12})
        self.assertEqual(plan['steps'], [{'op': 'keyed-shift', 'key': KEY, 'mode': 'repeat',
                                          'direction': 'subtract', 'reset': 'word'}])
        self.assertIn('Only LP2-54 remains eligible', recipe['scope_change'])

    def test_changed_alphabet_pin_page_hash_order_and_snapshot_rejected(self):
        for change in (
            lambda r: r['inputs'].update(alphabet_sha256='0' * 64),
            lambda r: r['inputs']['pages'][0].update(text_sha256='0' * 64),
            lambda r: r['inputs'].update(version='reviewed'),
        ):
            recipe = self.changed()
            change(recipe)
            with self.assertRaises(ValueError):
                self.validate(recipe)
        multiple = construct_followup(ROOT, identifier='order-check', title='Order fixture',
            question='Synthetic ordering check', scope_change='Two explicit page pins',
            limitation='A test fixture only', operations=[{'id':'affine','a':28,'b':28}],
            pages=['lp2-00','lp2-54'])
        multiple['inputs']['pages'].reverse()
        with self.assertRaisesRegex(ValueError, 'page order/id mismatch'):
            self.validate(multiple)
        # Hash validation reads the current source, rather than trusting only pins.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'data/pages').mkdir(parents=True)
            (root / 'data/index.json').write_bytes((ROOT / 'data/index.json').read_bytes())
            page = json.loads((ROOT / 'data/pages/lp2-54.json').read_text(encoding='utf-8'))
            page['raw'] += '\n'
            (root / 'data/pages/lp2-54.json').write_text(json.dumps(page), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'page text pin mismatch'):
                validate_followups([self.recipe], root)

    def test_control_protocol_tampering_and_failed_prefix_rejected(self):
        for change in (
            lambda r: r['control'].update(expected_result_sha256='0' * 64),
            lambda r: r['control'].update(label='Archived manuscript control'),
            lambda r: r['control']['task']['steps'][0].update(reset='page'),
            lambda r: r['control']['task']['alphabet'].reverse(),
        ):
            recipe = self.changed()
            change(recipe)
            recipe['control']['task']['taskId'] = runner.task_identity(recipe['control']['task'])
            with self.assertRaises(ValueError):
                self.validate(recipe)
        recipe = self.changed()
        task = recipe['control']['task']
        runes = [r['rune'] for r in task['alphabet']]
        source = task['pages'][0]['text']
        task['pages'][0]['text'] = runes[(runes.index(source[0]) + 1) % 29] + source[1:]
        task['taskId'] = runner.task_identity(task)
        # Even an honestly recomputed digest cannot authorize a failing control.
        recipe['control']['expected_result_sha256'] = digest(runner.run(task))
        with self.assertRaisesRegex(ValueError, 'failed exact-prefix'):
            self.validate(recipe)
        recipe = self.changed()
        wrong_key = [(n + 1) % 29 for n in KEY]
        recipe['card']['method']['value']['operations'][0]['key'] = wrong_key
        task = recipe['control']['task']
        task['steps'][0]['key'] = wrong_key
        task['taskId'] = runner.task_identity(task)
        recipe['control']['expected_result_sha256'] = digest(runner.run(task))
        with self.assertRaisesRegex(ValueError, 'failed exact-prefix'):
            self.validate(recipe)

    def test_unknown_rules_fields_criterion_and_key_rejected(self):
        mutations = [
            lambda r: r.update(arbitrary='extra'),
            lambda r: r['control'].update(expectedPlaintext='unregistered'),
            lambda r: r['card']['rules']['exceptionalCases'].update(status='specified', value='except F'),
            lambda r: r['card']['rules']['searchBounds'].update(status='unrestricted'),
            lambda r: r['card']['scope']['value'].update(description='first line only'),
            lambda r: r['card']['rules']['evaluation'].update(value={'kind': 'measurement'}),
            lambda r: r['card']['method']['value']['operations'][0].update(phase=1),
            lambda r: r['card']['unresolved'].append({'kind': 'unknown'}),
            lambda r: r['card'].update(version=True),
        ]
        for mutation in mutations:
            recipe = self.changed()
            mutation(recipe)
            with self.assertRaises(ValueError):
                self.validate(recipe)
        for key in ([True], [29], [], [1] * 257):
            recipe = self.changed()
            recipe['card']['method']['value']['operations'][0]['key'] = key
            recipe['control']['task']['steps'][0]['key'] = key
            recipe['control']['task']['taskId'] = runner.task_identity(recipe['control']['task'])
            with self.assertRaises(ValueError):
                self.validate(recipe)

    def test_production_card_compiler_and_full_js_result_parity(self):
        script = r'''
import fs from 'node:fs';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
import C from './claim-specification.js';import H from './claim-share.js';import L from './local-experiment.js';
import {validateCard} from './services/idea-assistant/idea-relations.mjs';
import {planCard} from './services/idea-assistant/prepare-task.mjs';
const f=JSON.parse(fs.readFileSync('experiments/records/lp2-known-vigenere-keys/record.json','utf8')).browser_followups[0];
assert.deepEqual(validateCard(f.card),f.card);
const p=planCard(f.card);assert(!p.reason,p.reason);assert.equal(p.inputVersion,f.inputs.version);
assert.deepEqual(p.pages,f.inputs.pages.map(p=>p.id));assert.deepEqual(p.steps,f.control.task.steps);
assert.deepEqual(p.criterion,f.control.task.criterion);await L.checkIdentity(f.control.task);
const result=L.run(f.control.task);assert(result.matches.every(m=>m.matched));
assert.equal(createHash('sha256').update(L.stable(result)).digest('hex'),f.control.expected_result_sha256);
process.stdout.write(JSON.stringify(result));
'''
        completed = subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT,
                                   capture_output=True, text=True, encoding='utf-8', check=True)
        self.assertEqual(json.loads(completed.stdout), runner.run(self.recipe['control']['task']))

    def test_builder_calls_optional_validation_without_target_execution(self):
        from unittest.mock import patch
        import build_experiments as builder
        pages = {p.stem for p in (ROOT / 'data/pages').glob('*.json')}
        original = builder.validate_followups
        with patch.object(builder, 'validate_followups', wraps=original) as validate, \
                patch.object(runner, 'run', wraps=runner.run) as run_control:
            builder.validate_record(ROOT, RECORD, pages)
            validate.assert_called_once()
            run_control.assert_called_once()
            self.assertEqual(run_control.call_args.args[0], self.recipe['control']['task'])
        recipe = self.changed()
        with self.assertRaisesRegex(ValueError, 'duplicate id'):
            validate_followups([recipe, recipe], ROOT)


if __name__ == '__main__':
    unittest.main()
