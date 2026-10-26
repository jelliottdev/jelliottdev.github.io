"""Pinned finite-bank compiler parity; never execute manuscript target programs."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import authored_finite_followups as authored
import browser_followups as fixed
import finite_followup_cards as finite
import finite_sequence_banks as banks
from test_finite_followup_cards import card as base_card, js

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / 'data/finite-sequence-banks.json').read_bytes())


def card(bank, offset=0, direction='subtract', reset='page'):
    value = base_card([{'id': 'finite_key_bank', 'label': 'Pinned finite key stream',
                       'bankId': bank['id'], 'bankSha256': bank['sha256'], 'offset': offset,
                       'direction': direction, 'reset': reset}], pages=['lp2-%02d' % i for i in range(56)])
    value['rules']['searchBounds'] = {'status': 'not_applicable'}
    return value


def family(bank):
    value = card(bank)
    for key in ('offset', 'direction', 'reset'):
        del value['method']['value']['operations'][0][key]
    value['rules']['searchBounds'] = {'status': 'specified', 'value': {'kind': 'finite-settings', 'version': 1,
        'parameters': [{'operation': 0, 'name': 'offset', 'values': list(range(29))},
                       {'operation': 0, 'name': 'direction', 'values': ['subtract', 'add']},
                       {'operation': 0, 'name': 'reset', 'values': ['page', 'line', 'word']}]}}
    return value


class FiniteBankCompilers(unittest.TestCase):
    def test_category_annotation_preserves_executable_program(self):
        value = card(MANIFEST['banks'][0], offset=7, reset='word')
        expected = fixed.compile_card(value)
        value['method']['value']['operations'][0]['declaredFamilyId'] = 'number-streams'
        self.assertEqual(fixed.compile_card(value), expected)
        code = "const fs=require('node:fs'),F=require('./fixed-plan-compiler.js'),c=F.compile(JSON.parse(fs.readFileSync(0,'utf8')));if(c.reason)throw Error(c.reason);console.log(JSON.stringify({pages:c.pages,steps:c.steps,inputVersion:c.inputVersion,criterion:c.criterion}));"
        actual = json.loads(subprocess.check_output(['node', '-e', code], input=json.dumps(value), cwd=ROOT, encoding='utf-8'))
        self.assertEqual(actual, expected)

    def test_all_four_banks_all_696_programs_match_actual_browser_compiler(self):
        cards, expected = [], []
        with patch.object(fixed.runner, 'run', side_effect=AssertionError('Compilation cannot run targets')):
            for bank in MANIFEST['banks']:
                for offset in range(29):
                    for direction in ('add', 'subtract'):
                        for reset in ('page', 'line', 'word'):
                            value = card(bank, offset, direction, reset)
                            before = copy.deepcopy(value)
                            compiled = fixed.compile_card(value)
                            self.assertEqual(compiled['steps'], [{'op': 'finite-shift', 'key': bank['values'][offset:],
                                                                 'direction': direction, 'reset': reset}])
                            self.assertEqual(len(compiled['steps'][0]['key']), 305 - offset)
                            self.assertEqual(value, before)
                            self.assertLess(len(fixed.stable(value).encode()), 12000)
                            cards.append(value)
                            expected.append(hashlib.sha256(fixed.stable(compiled).encode()).hexdigest())
        code = r"""const fs=require('node:fs'),crypto=require('node:crypto'),E=require('./local-experiment.js'),F=require('./fixed-plan-compiler.js');E.run=()=>{throw Error('No target execution');};const input=JSON.parse(fs.readFileSync(0,'utf8'));console.log(JSON.stringify(input.map(card=>{const c=F.compile(card);if(c.reason)throw Error(c.reason);const value={pages:c.pages,steps:c.steps,inputVersion:c.inputVersion,criterion:c.criterion};return crypto.createHash('sha256').update(E.stable(value)).digest('hex');})));"""
        actual = json.loads(subprocess.check_output(['node', '-e', code], input=json.dumps(cards), cwd=ROOT, encoding='utf-8'))
        self.assertEqual(len(actual), 696)
        self.assertEqual(actual, expected)

    def test_174_setting_families_fit_short_cards_and_independent_expansion(self):
        for bank in MANIFEST['banks']:
            value = family(bank)
            compiled = finite.compile_card(value)
            self.assertEqual(compiled['declaration']['programCount'], 174)
            self.assertEqual(compiled['declaration']['caseCount'], 9744)
            self.assertLess(len(fixed.stable(value).encode()), 12000)
            actual = js([value])[0]
            self.assertTrue(actual['ok'])
            self.assertEqual(finite.expand(value), actual['value'])
            for variant in compiled['variants']:
                op = variant['card']['method']['value']['operations'][0]
                self.assertEqual(variant['compiled']['steps'][0]['key'], banks.resolve(bank['id'], bank['sha256'], op['offset']))

    def test_full_warning_controls_use_finite_tails_and_never_execute_a_target(self):
        value = family(MANIFEST['banks'][0])
        executed = []
        run = fixed.runner.run
        def synthetic(task):
            self.assertEqual([p['id'] for p in task['pages']], ['lp1-01'])
            self.assertIn('synthetic', task['title'].lower())
            self.assertEqual(len(task['criterion']['values']), 184)
            self.assertEqual(task['steps'][0]['op'], 'finite-shift')
            executed.append(task['taskId'])
            return run(task)
        with patch.object(fixed.runner, 'run', side_effect=synthetic):
            recipe = authored.construct_followup(ROOT, card=value, identifier='software-finite-bank-control',
                title='Pinned finite bank test', question='Does the supplied finite stream produce the stated output?',
                scope_change='All explicitly declared settings.', limitation='Synthetic construction only; no manuscript outcomes.')
        self.assertEqual(len(set(executed)), 174)
        self.assertEqual(len(recipe['control']['members']), 174)
        self.assertLess(len(fixed.stable(recipe).encode()), 2 * 1024 * 1024)

    def test_unknown_hash_offset_irrelevant_fields_and_conflicting_global_rules_reject(self):
        bank = MANIFEST['banks'][0]
        mutations = [lambda o: o.update(bankId='unknown'), lambda o: o.update(bankSha256='0' * 64),
                     lambda o: o.update(offset=-1), lambda o: o.update(offset=29), lambda o: o.update(offset=True),
                     lambda o: o.update(offset=0.5), lambda o: o.update(label='Invented operation'),
                     lambda o: o.update(key=[1]), lambda o: o.update(a=1), lambda o: o.update(interrupts=[0]),
                     lambda o: o.update(extra=1), lambda o: o.update(direction='guess')]
        for mutate in mutations:
            value = card(bank)
            mutate(value['method']['value']['operations'][0])
            with self.subTest(value=value['method']), self.assertRaises(ValueError):
                fixed.compile_card(value)
        for rule, state in [('reset', {'status': 'specified', 'value': 'line'}),
                            ('reset', {'status': 'not_applicable'}), ('initialState', {'status': 'specified', 'value': 0})]:
            value = card(bank)
            value['rules'][rule] = state
            with self.assertRaises(ValueError):
                fixed.compile_card(value)
        for offsets in [[0, 0], [-1], [29], [True], [0.5]]:
            value = family(bank)
            value['rules']['searchBounds']['value']['parameters'][0]['values'] = offsets
            with self.assertRaises(ValueError):
                finite.compile_card(value)
        with patch.dict(sys.modules, {'finite_sequence_banks': None}):
            with self.assertRaisesRegex(ValueError, 'bank unavailable'):
                fixed.compile_card(card(bank))
            legacy = card(bank)
            legacy['method']['value']['operations'] = [{'id': 'affine', 'a': 28, 'b': 28}]
            self.assertEqual(fixed.compile_card(legacy)['steps'], [{'op': 'affine', 'a': 28, 'b': 28}])


if __name__ == '__main__':
    unittest.main()
