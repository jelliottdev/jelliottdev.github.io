"""Finite authored-card expansion parity; no manuscript decoding or target runs."""
import copy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import browser_followups as fixed
import finite_followup_cards as finite

ROOT = Path(__file__).resolve().parents[1]
NODE = r"""
const fs=require('fs'),F=require('./finite-settings.js'),C=require('./claim-specification.js'),H=require('./claim-share.js');
const cards=JSON.parse(fs.readFileSync(0,'utf8'));
console.log(JSON.stringify(cards.map(card=>{try{return {ok:true,value:F.factored.expand(card)}}catch(e){return {ok:false,error:e.message}}})));
"""


def known(value):
    return {'status': 'specified', 'value': value}


def card(operations=None, axes=None, pages=None):
    rules = {name: {'status': 'unspecified'} for name in fixed.RULES}
    for name, value in {'representation': 'GP29', 'wordBoundaries': 'preserve',
                        'unmapped': 'preserve', 'inputVersion': 'raw', 'evaluation': 'measurement',
                        'searchBounds': {'kind': 'finite-settings', 'version': 1,
                                         'parameters': axes or [{'operation': 0, 'name': 'a', 'values': [2, 1]}]}}.items():
        rules[name] = known(value)
    return {'version': 1, 'outcome': known({'outcomeId': 'decipher', 'detail': 'Decipher the text'}),
            'method': known({'operations': operations or [{'id': 'affine', 'b': 0}]}),
            'scope': known({'pages': pages or ['lp2-15']}), 'rules': rules, 'unresolved': []}


def js(cards):
    return json.loads(subprocess.check_output(['node', '-e', NODE], input=json.dumps(cards),
                                             cwd=ROOT, encoding='utf-8'))


class FiniteCards(unittest.TestCase):
    def test_real_42_program_known_keys_full_page_scope_exact_parity(self):
        plan = json.loads((ROOT / 'experiments/records/lp2-known-vigenere-keys/plan.json').read_text(encoding='utf-8'))
        keys = [key['indices'][phase:] + key['indices'][:phase]
                for key in plan['keys'] for phase in range(len(key['indices']))]
        source = card([{'id': 'repeating_key', 'reset': 'page'}],
                      [{'operation': 0, 'name': 'key', 'values': list(reversed(keys))},
                       {'operation': 0, 'name': 'direction', 'values': ['subtract', 'add']}], plan['pages'])
        before = copy.deepcopy(source)
        with patch.object(fixed.runner, 'run', side_effect=AssertionError('No target execution')):
            actual = finite.expand(source)
            compiled = finite.compile_card(source)
        expected = js([source])[0]
        self.assertTrue(expected['ok']); self.assertEqual(actual, expected['value'])
        self.assertEqual(actual['declaration']['programCount'], 42)
        self.assertEqual(actual['declaration']['caseCount'], 2352)
        self.assertEqual(source, before)
        for item in compiled['variants']:
            self.assertEqual(item['compiled']['pages'], plan['pages'])
            self.assertEqual(item['compiled'], fixed.compile_card(item['card']))
            self.assertEqual(item['card']['rules']['searchBounds'], {'status': 'not_applicable'})
            for name in fixed.RULES:
                if name != 'searchBounds': self.assertEqual(item['card']['rules'][name], source['rules'][name])

    def test_all_axes_ordering_operation_targets_and_fixed_parameters_preserved(self):
        source = card([
            {'id': 'affine'},
            {'id': 'interrupted_repeating_key', 'label': 'Interrupted repeating key'},
            {'id': 'reverse_runes', 'label': 'Reverse rune order within each word'}], [
                {'operation': 2, 'name': 'unit', 'values': ['word']},
                {'operation': 1, 'name': 'interrupts', 'values': [[0, 3], [0], [2]]},
                {'operation': 1, 'name': 'reset', 'values': ['word', 'page', 'line']},
                {'operation': 1, 'name': 'direction', 'values': ['subtract', 'add']},
                {'operation': 1, 'name': 'key', 'values': [[1, 2], [1], [0, 28]]},
                {'operation': 0, 'name': 'b', 'values': [28, 0]},
                {'operation': 0, 'name': 'a', 'values': [10, 2]}], ['lp2-00', 'lp2-54'])
        expected = js([source])[0]; self.assertTrue(expected['ok'])
        actual = finite.expand(source); self.assertEqual(actual, expected['value'])
        self.assertEqual(actual['declaration']['programCount'], 216)
        self.assertEqual([a['name'] for a in actual['declaration']['parameters']],
                         ['a', 'b', 'direction', 'interrupts', 'key', 'reset', 'unit'])

    def test_same_duplicate_fixed_conflict_invalid_axis_and_canonical_rejections_as_js(self):
        base = card(); cases = []
        def add(change):
            value = copy.deepcopy(base); change(value); cases.append(value)
        axes = lambda c: c['rules']['searchBounds']['value']['parameters']
        add(lambda c: axes(c).append(copy.deepcopy(axes(c)[0])))
        add(lambda c: axes(c)[0].update(values=[1, 1]))
        add(lambda c: axes(c)[0].update(values=[True]))
        add(lambda c: axes(c)[0].update(values=[-1]))
        add(lambda c: axes(c)[0].update(values=[29]))
        add(lambda c: axes(c)[0].update(operation=1))
        add(lambda c: axes(c)[0].update(operation=True))
        add(lambda c: axes(c)[0].update(name='unknown'))
        add(lambda c: axes(c)[0].update(extra=0))
        add(lambda c: c['method']['value']['operations'][0].update(a=1))
        add(lambda c: c['scope']['value'].update(pages=['lp2-16', 'lp2-15']))
        add(lambda c: c['scope']['value'].update(pages=['lp2-15', 'lp2-15']))
        add(lambda c: c['scope']['value'].update(pages=['lp2-58']))
        add(lambda c: c['scope']['value'].update(description='Not exact pages only'))
        add(lambda c: c.update(extra=True))
        add(lambda c: c['method']['value']['operations'][0].update(sourceText='hidden wording'))
        add(lambda c: c['outcome']['value'].update(outcomeId='unclassified', detail='Solve LP2!'))
        add(lambda c: c['rules']['searchBounds']['value'].update(version=2))
        add(lambda c: c['rules']['searchBounds']['value'].update(extra=1))
        add(lambda c: c['rules']['searchBounds'].update(provenance={}))
        for value, expected in zip(cases, js(cases)):
            with self.subTest(value=value):
                self.assertFalse(expected['ok'])
                with self.assertRaises(ValueError): finite.expand(value)

    def test_literal_array_boundary_and_direction_rejections_match_js(self):
        cases = []
        for name, values in [('key', [[]]), ('key', [[29]]), ('key', [[False]]),
                             ('interrupts', [[1, 0]]), ('interrupts', [[1, 1]]),
                             ('interrupts', [[]]), ('direction', ['multiply']),
                             ('reset', ['section']), ('unit', ['character'])]:
            cases.append(card([{'id': 'repeating_key'}], [{'operation': 0, 'name': name, 'values': values}]))
        for value, expected in zip(cases, js(cases)):
            self.assertFalse(expected['ok'])
            with self.assertRaises(ValueError): finite.expand(value)

    def test_limit_boundaries_and_no_truncation(self):
        pages = ['lp1-' + str(i).zfill(2) for i in range(17)] + ['lp2-' + str(i).zfill(2) for i in range(58)]
        # 4^5=1024 exactly, all 75 pages: factored ceiling 76800.
        source = card([{'id': 'affine'} for _ in range(3)], [
            {'operation': op, 'name': name, 'values': list(range(4))}
            for op, name in [(0, 'a'), (0, 'b'), (1, 'a'), (1, 'b'), (2, 'a')]], pages)
        source['method']['value']['operations'][2]['b'] = 0
        expected = js([source])[0]; self.assertTrue(expected['ok'])
        actual = finite.expand(source); self.assertEqual(actual, expected['value'])
        self.assertEqual(actual['declaration']['caseCount'], 76800)
        too_many = copy.deepcopy(source)
        too_many['rules']['searchBounds']['value']['parameters'][0]['values'].append(4)
        self.assertFalse(js([too_many])[0]['ok'])
        with self.assertRaisesRegex(ValueError, '1024'): finite.expand(too_many)

    def test_card_structure_byte_expansion_and_unsafe_data_bounds(self):
        cases = []
        for name, value in [('constructor', 1), ('__proto__', {})]:
            c = card(); c['method']['value']['operations'][0][name] = value; cases.append(c)
        c = card(); c['outcome']['value']['detail'] = 'x' * 12000; cases.append(c)
        c = card(); nested = {}; c['rules']['initialState'] = known(nested)
        for _ in range(18): nested['x'] = {}; nested = nested['x']
        cases.append(c)
        # Individually valid small card, but 1024 repeated detached cards exceed 8MiB.
        c = card([{'id': 'affine'} for _ in range(3)], [
            {'operation': op, 'name': name, 'values': list(range(4))}
            for op, name in [(0, 'a'), (0, 'b'), (1, 'a'), (1, 'b'), (2, 'a')]])
        c['method']['value']['operations'][2]['b'] = 0
        c['outcome']['value']['detail'] = 'x' * 8000; cases.append(c)
        for c, expected in zip(cases, js(cases)):
            self.assertFalse(expected['ok'])
            with self.assertRaises(ValueError): finite.expand(c)

    def test_fixed_compiler_remains_authority_and_unsupported_members_are_not_rewritten(self):
        source = card([{'id': 'reverse_runes', 'label': 'Reverse rune order within each word'}],
                      [{'operation': 0, 'name': 'unit', 'values': ['word', 'line']}])
        self.assertTrue(js([source])[0]['ok'])
        with self.assertRaisesRegex(ValueError, 'reverse wording'): finite.expand(source)
        source = card(); source['rules']['reset'] = known('word')
        with self.assertRaisesRegex(ValueError, 'unused reset'): finite.expand(source)
        source = card(); source['rules']['evaluation'] = known({'kind': 'readability'})
        with self.assertRaises(ValueError): finite.expand(source)
        source = card([{'id': 'repeating_key', 'key': [0, 1], 'direction': 'subtract'}],
                      [{'operation': 0, 'name': 'reset', 'values': ['word', 'page']}])
        source['rules']['reset'] = known('word')
        with self.assertRaisesRegex(ValueError, 'conflicting reset'): finite.expand(source)

    def test_python_non_json_values_and_nonfinite_numbers_are_refused(self):
        for value in [float('nan'), float('inf'), 10 ** 1000, ('not', 'JSON'), object()]:
            source = card(); source['outcome']['value']['detail'] = value
            with self.subTest(type=type(value)), self.assertRaises(ValueError): finite.expand(source)


if __name__ == '__main__':
    unittest.main()
