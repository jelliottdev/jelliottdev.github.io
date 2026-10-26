"""Exact source bounds, control witnesses and one-rule extension; no targets run."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import authored_finite_followups as authored
import browser_followups as fixed
import finite_followup_cards as finite
import panel_prime_followups as panel
from research_questions import validate_research_questions


class PanelPrimeFollowups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = panel.ROOT / 'experiments/records/lp2-panel-prime-openings/record.json'
        cls.before = cls.path.read_bytes()
        cls.original = json.loads(cls.before)
        original_run = fixed.runner.run
        cls.executed = []
        def synthetic_only(task):
            if [p['id'] for p in task['pages']] != ['lp1-01'] or 'synthetic' not in task['title'].lower():
                raise AssertionError('generator executed a manuscript target')
            if len(task['criterion']['values']) != 184:
                raise AssertionError('control does not check full Warning')
            cls.executed.append(task['taskId'])
            return original_run(task)
        with patch.object(fixed.runner, 'run', side_effect=synthetic_only):
            cls.proposed = panel.build()
        cls.language, cls.words, cls.lines = cls.proposed['browser_followups'][-3:]

    def test_only_synthetic_controls_and_source_unchanged(self):
        self.assertTrue(self.executed)
        self.assertEqual(self.path.read_bytes(), self.before)
        expected = copy.deepcopy(self.proposed)
        for name in ('browser_followups', 'research_questions'):
            if name in self.original:
                expected[name] = self.original[name]
            else:
                del expected[name]
        self.assertEqual(expected, self.original)
        self.assertLess(len(json.dumps(self.proposed, ensure_ascii=False).encode()), 512 * 1024)

    def test_exact_program_geometry_and_maintained_criterion(self):
        plan = panel.source()
        base = [n % 29 for n in plan['key']]
        for recipe in (self.language, self.words, self.lines):
            expanded = finite.compile_card(recipe['card'])
            self.assertEqual(expanded['declaration']['programCount'], 32)
            self.assertEqual(expanded['declaration']['caseCount'], 1792)
            actual = {(tuple(v['compiled']['steps'][0]['key']), v['compiled']['steps'][0]['direction'])
                      for v in expanded['variants']}
            self.assertEqual(actual, {(tuple(base[i:] + base[:i]), direction)
                                     for i in range(16) for direction in ('add', 'subtract')})
            self.assertEqual(recipe['card']['scope']['value']['pages'], panel.PAGES)
            self.assertEqual(recipe['card']['rules']['evaluation']['value'], fixed.LANGUAGE_CRITERION)
            self.assertEqual(recipe['inputs']['pages'][50]['id'], 'lp2-50')
            authored.validate_recipe(recipe, panel.ROOT, set(panel.PAGES))
            self.assertEqual(len(recipe['control']['members']), 32)

    def test_one_changed_rule_and_identical_inputs(self):
        for reset, recipe in [('word', self.words), ('line', self.lines)]:
            changed = copy.deepcopy(self.language['card'])
            changed['method']['value']['operations'][0]['reset'] = reset
            self.assertEqual(changed, recipe['card'])
            self.assertEqual(self.language['inputs'], recipe['inputs'])
        with patch.object(panel.boundary, 'variants', wraps=panel.boundary.variants) as helper:
            self.assertEqual(panel.candidate('line'), self.lines)
        helper.assert_called_once_with(self.language['card'], operation_index=0, allowed_resets=['line'])
        self.assertIn('Each non-rune mark ends a word', self.words['limitation'])
        self.assertIn('new evaluation of existing outputs', self.language['limitation'])
        self.assertIn('line breaks, but not at spaces or punctuation', self.lines['limitation'])
        self.assertIn('No result', self.lines['limitation'])

    def test_existing_recipes_are_exact_and_old_recipe_drift_is_rejected(self):
        installed = {r['id']: r for r in self.original.get('browser_followups', [])}
        for recipe in (self.language, self.words):
            if recipe['id'] in installed:
                self.assertEqual(recipe, installed[recipe['id']])
        self.assertEqual([r['id'] for r in self.proposed['browser_followups']][-3:],
                         ['panel-primes-language-comparison', 'panel-primes-word-reset-language', 'panel-primes-line-reset-language'])
        bad = copy.deepcopy(self.original)
        bad['browser_followups'] = [copy.deepcopy(self.language)]
        bad['browser_followups'][0]['title'] = 'Changed older recipe'
        original = Path.read_bytes
        def altered(path):
            return json.dumps(bad, ensure_ascii=False).encode('utf8') if path == self.path else original(path)
        with patch.object(Path, 'read_bytes', altered):
            with self.assertRaisesRegex(ValueError, 'existing panel recipe changed'):
                panel.build()

    def test_questions_open_derived_not_duplicated(self):
        questions = self.proposed['research_questions'][-3:]
        self.assertEqual(questions, panel.questions())
        self.assertTrue(all(q['state'] == 'open' and 'question' not in q for q in questions))
        validate_research_questions(questions, self.proposed, strict_authoring=True)
        bad = copy.deepcopy(questions)
        bad[0]['question'] = 'A different question?'
        with self.assertRaisesRegex(ValueError, 'conflicts with followup'):
            validate_research_questions(bad, self.proposed, strict_authoring=True)

    def test_source_pin_and_official_raw_mutations_rejected(self):
        original = Path.read_bytes
        mutations = [
            ('experiments/records/lp2-panel-prime-openings/plan.json', lambda value: value + b' '),
            ('exports/fibonacci-prime-panel.json', lambda value: value + b' '),
            ('text/lp2-00.txt', lambda value: value + b' '),
            ('data/pages/lp2-00.json', lambda value: json.dumps({**json.loads(value), 'raw': 'altered'}).encode()),
            ('data/local-run-inputs.json', lambda value: json.dumps({**json.loads(value), 'alphabet': []}).encode())]
        for name, mutate in mutations:
            target = panel.ROOT / name
            def injected(path):
                value = original(path)
                return mutate(value) if path == target else value
            with self.subTest(path=name), patch.object(Path, 'read_bytes', injected):
                with self.assertRaises(ValueError):
                    panel.source()

    def test_controls_fail_closed_on_mutation(self):
        for field in ('settings', 'expected', 'input'):
            bad = copy.deepcopy(self.language)
            if field == 'settings':
                bad['control']['members'][0]['settings'] = []
            elif field == 'expected':
                bad['control']['members'][0]['control']['expected_result_sha256'] = '0' * 64
            else:
                bad['inputs']['pages'][0]['text_sha256'] = '0' * 64
            with self.subTest(field=field), self.assertRaises(ValueError):
                authored.validate_recipe(bad, panel.ROOT, set(panel.PAGES))


if __name__ == '__main__':
    unittest.main()
