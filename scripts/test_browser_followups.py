"""Authored recipe validation; only synthetic data is transformed, never targets."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from browser_followups import (KEY, WARNING12, alphabet, compile_card,
                               construct_second_koan_word_reset, digest,
                               text_hash, validate_followups, runner)

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

    def test_constructor_reproduces_exact_authored_recipe_without_targets(self):
        self.assertEqual(construct_second_koan_word_reset(ROOT), self.recipe)
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
        expected = ['lp2-' + str(n).zfill(2) for n in range(56) if n != 50]
        self.assertEqual([p['id'] for p in recipe['inputs']['pages']], expected)
        plan = compile_card(recipe['card'])
        self.assertEqual(plan['pages'], expected)
        self.assertEqual(plan['criterion'], {'kind': 'exact-prefix', 'values': WARNING12})
        self.assertEqual(plan['steps'], [{'op': 'keyed-shift', 'key': KEY, 'mode': 'repeat',
                                          'direction': 'subtract', 'reset': 'word'}])
        self.assertIn('not the original nine-opening', recipe['scope_change'])

    def test_changed_alphabet_pin_page_hash_order_and_snapshot_rejected(self):
        for change in (
            lambda r: r['inputs'].update(alphabet_sha256='0' * 64),
            lambda r: r['inputs']['pages'][0].update(text_sha256='0' * 64),
            lambda r: r['inputs']['pages'].reverse(),
            lambda r: r['inputs'].update(version='reviewed'),
        ):
            recipe = self.changed()
            change(recipe)
            with self.assertRaises(ValueError):
                self.validate(recipe)
        # Hash validation reads the current source, rather than trusting only pins.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'data/pages').mkdir(parents=True)
            (root / 'data/index.json').write_bytes((ROOT / 'data/index.json').read_bytes())
            page = json.loads((ROOT / 'data/pages/lp2-00.json').read_text(encoding='utf-8'))
            page['raw'] += '\n'
            (root / 'data/pages/lp2-00.json').write_text(json.dumps(page), encoding='utf-8')
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
