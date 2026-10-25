"""Validate direct-reading control declarations; execute synthetic fixtures only."""
import copy
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import patch

from browser_followups import (alphabet, compile_card, construct_word_pair_followup,
                               digest, runner, text_hash, validate_followups)

ROOT = Path(__file__).resolve().parents[1]
SPECS = (
    ('word-internal-affine-all-lags', 'direct-reading-lag-five-control', 5, 1, 0),
    ('word-internal-affine-lags', 'direct-reading-lag-six-control', 6, 27, 24),
)


def direct_pages():
    evidence = json.loads((ROOT / 'data/evidence/known-readings.json').read_text(encoding='utf-8'))
    return sorted({page for reading in evidence['controls'] if reading['method'] == 'direct'
                   for page in reading['pages']})


def independent_synthetic_result(task):
    """Enumerate ordered distinct positions, independently of runner count routines."""
    assert task['steps'] == []
    assert 'synthetic' in task['title'].lower()
    criterion = task['criterion']
    assert criterion['boundaries'] == 'hyphen-period'
    indices = {entry['rune']: i for i, entry in enumerate(task['alphabet'])}
    lag, a, b = (criterion[key] for key in ('lag', 'a', 'b'))
    frequencies = Counter()
    total = adjacent = equal = opportunities = matches = 0
    expectation = Fraction(0)
    transformed, page_rows = [], []
    for page in task['pages']:
        text = page['text']
        values = [indices[ch] for ch in text if ch in indices]
        frequencies.update(values)
        total += len(values)
        adjacent += max(0, len(values) - 1)
        equal += sum(left == right for left, right in zip(values, values[1:]))
        transformed.append({'page': page['id'], 'text': text})
        page_opportunities = page_matches = 0
        page_expectation = Fraction(0)
        for segment in re.split(r'[-.]', text):
            word = [indices[ch] for ch in segment if ch in indices]
            count = max(0, len(word) - lag)
            page_opportunities += count
            page_matches += sum((a * word[i] + b) % 29 == word[i + lag]
                                for i in range(count))
            if count:
                # Sample every ordered pair of distinct positions uniformly.
                favorable = sum((a * left + b) % 29 == right
                                for i, left in enumerate(word)
                                for j, right in enumerate(word) if i != j)
                page_expectation += Fraction(count * favorable, len(word) * (len(word) - 1))
        page_rows.append({'page': page['id'], 'opportunities': page_opportunities,
                          'matches': page_matches, 'expected': rational(page_expectation)})
        opportunities += page_opportunities
        matches += page_matches
        expectation += page_expectation
    return {'schema': 'liberpedia-local-result-v1', 'taskId': task['taskId'], 'engine': task['engine'],
            'metrics': {'pages': len(task['pages']), 'runes': total, 'adjacentPairs': adjacent,
                        'equalAdjacentPairs': equal,
                        'ioc': sum(n * (n - 1) for n in frequencies.values()) / (total * (total - 1))
                        if total > 1 else 0.0},
            'matches': [], 'transformed': transformed, 'runnerVersion': '1',
            'wordPairs': {'opportunities': opportunities, 'matches': matches,
                          'expected': rational(expectation), 'pages': page_rows}}


def rational(value):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


class DirectReadingFollowups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = direct_pages()
        cls.recipes = []
        for record_id, recipe_id, lag, a, b in SPECS:
            record = json.loads((ROOT / 'experiments/records' / record_id / 'record.json').read_text(encoding='utf-8'))
            matches = [item for item in record.get('browser_followups', []) if item['id'] == recipe_id]
            if len(matches) != 1:
                raise AssertionError('Expected exactly one authored recipe: ' + recipe_id)
            cls.recipes.append(matches[0])

    def test_scope_is_derived_only_from_direct_known_readings(self):
        self.assertEqual(self.pages, ['lp1-05', 'lp1-10', 'lp1-11', 'lp1-12', 'lp1-13', 'lp1-16', 'lp2-57'])
        evidence = json.loads((ROOT / 'data/evidence/known-readings.json').read_text(encoding='utf-8'))
        encrypted = {page for reading in evidence['controls'] if reading['method'] != 'direct'
                     for page in reading['pages']}
        self.assertFalse(encrypted.intersection(self.pages))
        for recipe, (_, _, lag, a, b) in zip(self.recipes, SPECS):
            plan = compile_card(recipe['card'])
            self.assertEqual(plan, {'pages': self.pages, 'steps': [], 'inputVersion': 'raw',
                                   'criterion': {'kind': 'word-affine-count', 'lag': lag, 'a': a,
                                                 'b': b, 'boundaries': 'hyphen-period'}})
            operations = recipe['card']['method']['value']['operations']
            self.assertEqual(operations, [{'id': 'word_affine_count', 'label': 'Within-word affine pair count',
                                         'lag': lag, 'a': a, 'b': b, 'boundaries': 'hyphen-period'}])
            self.assertEqual(recipe['inputs']['version'], 'raw')
            self.assertEqual(recipe['inputs']['alphabet_sha256'], digest(alphabet(ROOT)))
            expected = []
            for page_id in self.pages:
                page = json.loads((ROOT / 'data/pages' / (page_id + '.json')).read_text(encoding='utf-8'))
                self.assertEqual(page['id'], page_id)
                expected.append({'id': page_id, 'text_sha256': text_hash(page['raw'])})
            self.assertEqual(recipe['inputs']['pages'], expected)

    def test_standard_validation_executes_only_exact_synthetic_control(self):
        original = runner.run
        for recipe in self.recipes:
            before = copy.deepcopy(recipe)
            calls = []
            def synthetic_only(task):
                self.assertEqual(task, recipe['control']['task'])
                self.assertIn('synthetic', task['title'].lower())
                calls.append(task)
                return original(task)
            with patch.object(runner, 'run', side_effect=synthetic_only):
                self.assertEqual(validate_followups([recipe], ROOT), [recipe])
            self.assertEqual(len(calls), 1)
            self.assertEqual(recipe, before)

    def test_synthetic_complete_result_has_independent_python_and_javascript_parity(self):
        expected = []
        for recipe in self.recipes:
            task = recipe['control']['task']
            result = independent_synthetic_result(task)
            self.assertEqual(result, runner.run(task))
            self.assertEqual(digest(result), recipe['control']['expected_result_sha256'])
            self.assertGreater(result['wordPairs']['matches'], 0)
            self.assertEqual(result['wordPairs']['matches'], result['wordPairs']['opportunities'])
            expected.append(result)
        script = r"""
import fs from 'node:fs';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
import L from './local-experiment.js';import Compiler from './fixed-plan-compiler.js';
const {recipes,expected}=JSON.parse(fs.readFileSync(0,'utf8'));
for(let i=0;i<recipes.length;i++){
 const recipe=recipes[i],task=recipe.control.task,plan=Compiler.compile(recipe.card);
 assert(!plan.reason,plan.reason);assert.deepEqual(plan.steps,[]);
 assert.deepEqual(plan.criterion,task.criterion);assert.equal(plan.inputVersion,'raw');
 assert.deepEqual(plan.pages,recipe.inputs.pages.map(row=>row.id));
 assert(task.title.toLowerCase().includes('synthetic'));
 await L.checkIdentity(task);const result=L.run(task);
 assert.deepEqual(result,expected[i]);
 assert.equal(createHash('sha256').update(L.stable(result)).digest('hex'),recipe.control.expected_result_sha256);
}process.stdout.write(JSON.stringify({syntheticControls:recipes.length}));
"""
        completed = subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT,
                                   input=json.dumps({'recipes': self.recipes, 'expected': expected}, ensure_ascii=False),
                                   capture_output=True, text=True, encoding='utf-8', check=True)
        self.assertEqual(json.loads(completed.stdout), {'syntheticControls': 2})

    def test_pin_program_and_control_mutations_fail_closed(self):
        for recipe in self.recipes:
            mutations = [
                lambda r: r['inputs']['pages'][0].update(text_sha256='0' * 64),
                lambda r: r['inputs'].update(alphabet_sha256='0' * 64),
                lambda r: r['inputs']['pages'].reverse(),
                lambda r: r['inputs']['pages'].pop(),
                lambda r: r['card']['scope']['value']['pages'].append('lp1-01'),
                lambda r: r['card']['method']['value']['operations'][0].update(lag=4),
                lambda r: r['card']['rules']['evaluation']['value'].update(boundaries='non-rune'),
                lambda r: r['control'].update(expected_result_sha256='0' * 64),
                lambda r: r['control']['task'].update(steps=[{'op': 'affine', 'a': 1, 'b': 0}]),
            ]
            for mutate in mutations:
                bad = copy.deepcopy(recipe)
                mutate(bad)
                with self.assertRaises(ValueError):
                    validate_followups([bad], ROOT)

    def test_authoring_executes_synthetic_data_only(self):
        original = runner.run
        raw_targets = {json.loads((ROOT / 'data/pages' / (page + '.json')).read_text(encoding='utf-8'))['raw']
                       for page in self.pages}
        for recipe, (_, _, lag, a, b) in zip(self.recipes, SPECS):
            calls = []
            def synthetic_only(task):
                self.assertIn('synthetic', task['title'].lower())
                self.assertEqual(task['steps'], [])
                self.assertTrue(all(page['id'] == 'lp1-01' and page['text'] not in raw_targets
                                    for page in task['pages']))
                calls.append(task)
                return original(task)
            with patch.object(runner, 'run', side_effect=synthetic_only):
                authored = construct_word_pair_followup(ROOT, identifier=recipe['id'], title=recipe['title'],
                    question=recipe['question'], scope_change=recipe['scope_change'], limitation=recipe['limitation'],
                    pages=self.pages, lag=lag, a=a, b=b, boundaries='hyphen-period', input_version='raw')
            self.assertGreater(len(calls), 0)
            expected = copy.deepcopy(recipe)
            expected.pop('motivation', None)
            self.assertEqual(authored, expected)


if __name__ == '__main__':
    unittest.main()
