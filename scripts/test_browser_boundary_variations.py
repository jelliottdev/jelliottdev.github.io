"""Source-only restart variation parity and conservative failure bounds."""
import copy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import browser_boundary_variations as boundary
import browser_followups as fixed
import finite_followup_cards as finite
from test_finite_followup_cards import card, js

ROOT = Path(__file__).resolve().parents[1]


def source(identifier='repeating_key'):
    operation = {'id': identifier, 'key': [4, 2, 28], 'direction': 'subtract', 'reset': 'page'}
    if identifier == 'finite_key_bank':
        import finite_sequence_banks as banks
        manifest = json.loads((ROOT / 'data/finite-sequence-banks.json').read_bytes())
        bank = manifest['banks'][0]
        operation = {'id': identifier, 'bankId': bank['id'], 'bankSha256': bank['sha256'],
                     'offset': 0, 'direction': 'subtract', 'reset': 'page'}
    if identifier == 'interrupted_repeating_key':
        operation.update(label='Interrupted repeating key', interrupts=[0, 3])
    value = card([operation])
    value['rules']['searchBounds'] = {'status': 'not_applicable'}
    return value


class BoundaryVariations(unittest.TestCase):
    def test_fixed_replacement_changes_only_selected_reset_for_all_supported_ops(self):
        for operation in sorted(boundary.OPERATIONS):
            value = source(operation)
            before = copy.deepcopy(value)
            with patch.object(fixed.runner, 'run', side_effect=AssertionError('No execution')):
                rows = boundary.variants(value, operation_index=0, allowed_resets=['word', 'line'])
            self.assertEqual([row['reset'] for row in rows], ['line', 'word'])
            for row in rows:
                expected = copy.deepcopy(before)
                expected['method']['value']['operations'][0]['reset'] = row['reset']
                self.assertEqual(row['card'], expected)
                self.assertEqual(row['compiled'], fixed.compile_card(expected))
            self.assertEqual(value, before)

    def test_fixed_family_matches_independent_js_expansion(self):
        for identifier in sorted(boundary.OPERATIONS):
            value = source(identifier)
            generated = boundary.family(value, operation_index=0, allowed_resets=['word', 'page', 'line'])
            expected = copy.deepcopy(value)
            del expected['method']['value']['operations'][0]['reset']
            expected['rules']['searchBounds'] = {'status': 'specified', 'value': {
                'kind': 'finite-settings', 'version': 1, 'parameters': [
                    {'operation': 0, 'name': 'reset', 'values': ['line', 'page', 'word']}]}}
            self.assertEqual(generated['card'], expected)
            parity = js([expected])[0]
            self.assertTrue(parity['ok'])
            self.assertEqual(finite.expand(expected), parity['value'])

    def test_existing_axes_and_other_operations_are_preserved(self):
        value = card([{'id': 'affine', 'b': 3}, {'id': 'repeating_key', 'reset': 'page'}], [
            {'operation': 1, 'name': 'key', 'values': [[4, 2], [1]]},
            {'operation': 0, 'name': 'a', 'values': [1, 28]},
            {'operation': 1, 'name': 'direction', 'values': ['subtract', 'add']}])
        before = copy.deepcopy(value)
        generated = boundary.family(value, operation_index=1, allowed_resets=['word', 'page'])
        self.assertEqual(generated['card']['rules']['searchBounds']['value']['parameters'][:-1],
                         before['rules']['searchBounds']['value']['parameters'])
        self.assertEqual(generated['compiled']['declaration']['programCount'], 16)
        for row in boundary.variants(value, operation_index=1, allowed_resets=['word']):
            expected = copy.deepcopy(value)
            expected['method']['value']['operations'][1]['reset'] = 'word'
            self.assertEqual(row['card'], expected)
            self.assertEqual(row['compiled']['declaration']['programCount'], 8)
        self.assertEqual(value, before)

    def test_existing_axis_exact_explicit_choices_and_sole_axis_becomes_fixed(self):
        combined = boundary.family(source(), operation_index=0, allowed_resets=['page', 'word'])['card']
        before = copy.deepcopy(combined)
        self.assertEqual(boundary.family(combined, operation_index=0, allowed_resets=['word', 'page'])['card'], before)
        for row in boundary.variants(combined, operation_index=0, allowed_resets=['word', 'page']):
            self.assertEqual(row['card']['rules']['searchBounds'], {'status': 'not_applicable'})
            self.assertEqual(row['compiled'], fixed.compile_card(row['card']))
        with self.assertRaisesRegex(ValueError, 'exactly match'):
            boundary.family(combined, operation_index=0, allowed_resets=['word'])
        self.assertEqual(combined, before)

    def test_existing_selected_axis_removed_without_touching_other_axes(self):
        value = source()
        del value['method']['value']['operations'][0]['direction']
        value['rules']['searchBounds'] = {'status': 'specified', 'value': {
            'kind': 'finite-settings', 'version': 1, 'parameters': [
                {'operation': 0, 'name': 'direction', 'values': ['subtract', 'add']}]}}
        combined = boundary.family(value, operation_index=0, allowed_resets=['line', 'word'])['card']
        for row in boundary.variants(combined, operation_index=0, allowed_resets=['word', 'line']):
            self.assertEqual(row['card']['rules']['searchBounds'], value['rules']['searchBounds'])
            self.assertEqual(row['compiled']['declaration']['programCount'], 2)

    def test_explicit_global_conflicts_and_unsupported_operations_rejected(self):
        for name in ('reset', 'boundaryMode'):
            value = source()
            value['rules'][name] = {'status': 'specified', 'value': 'page' if name == 'reset' else 'within_words'}
            with self.assertRaisesRegex(ValueError, 'global'):
                boundary.family(value, operation_index=0, allowed_resets=['word'])
        for identifier in ('cumulative_difference', 'affine', 'word_prime_sums', 'unknown'):
            value = source()
            value['method']['value']['operations'][0]['id'] = identifier
            with self.assertRaisesRegex(ValueError, 'supported keyed restart'):
                boundary.family(value, operation_index=0, allowed_resets=['word'])

    def test_author_choices_and_original_declaration_must_be_valid(self):
        for choices in ([], ['word', 'word'], ['paragraph'], 'word', [True], {'word'}):
            with self.subTest(choices=choices), self.assertRaises(ValueError):
                boundary.variants(source(), operation_index=0, allowed_resets=choices)
        for index in (True, -1, 1, '0'):
            with self.assertRaises(ValueError):
                boundary.family(source(), operation_index=index, allowed_resets=['word'])
        value = source()
        del value['method']['value']['operations'][0]['reset']
        with self.assertRaises((ValueError, KeyError)):
            boundary.family(value, operation_index=0, allowed_resets=['word'])

    def test_combined_program_limit_rejected_without_truncation(self):
        value = card([{'id': 'affine'}, {'id': 'repeating_key', 'key': [1], 'direction': 'subtract', 'reset': 'page'}], [
            {'operation': 0, 'name': 'a', 'values': list(range(1, 29))},
            {'operation': 0, 'name': 'b', 'values': list(range(29))}])
        self.assertEqual(finite.compile_card(value)['declaration']['programCount'], 812)
        before = copy.deepcopy(value)
        with self.assertRaisesRegex(ValueError, '1024 programs'):
            boundary.family(value, operation_index=1, allowed_resets=['page', 'word'])
        self.assertEqual(value, before)

    def test_real_known_key_cards_keep_exact_inputs_evaluation_and_programs(self):
        record = json.loads((ROOT / 'experiments/records/lp2-known-vigenere-keys/record.json').read_bytes())
        value = next(r['card'] for r in record['browser_followups'] if r['id'] == 'known-keys-language-comparison')
        before = copy.deepcopy(value)
        with patch.object(fixed.runner, 'run', side_effect=AssertionError('No controls or targets')):
            combined = boundary.family(value, operation_index=0, allowed_resets=['page', 'word'])
            rows = boundary.variants(combined['card'], operation_index=0, allowed_resets=['word', 'page'])
        self.assertEqual(combined['compiled']['declaration']['programCount'], 84)
        self.assertEqual(combined['compiled']['declaration']['caseCount'], 4704)
        self.assertEqual(next(row['card'] for row in rows if row['reset'] == 'page'), value)
        for row in rows:
            self.assertEqual(row['card']['scope'], before['scope'])
            self.assertEqual(row['card']['rules']['evaluation'], before['rules']['evaluation'])
            self.assertEqual(row['card']['rules']['inputVersion'], before['rules']['inputVersion'])
        self.assertEqual(value, before)


if __name__ == '__main__':
    unittest.main()
