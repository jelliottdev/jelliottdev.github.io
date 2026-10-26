"""Source-owned declarations, exact controls and the one-rule extension bound."""
import copy
import json
import unittest
from unittest.mock import patch

import authored_finite_followups as authored
import browser_followups as fixed
import finite_followup_cards as finite
import known_key_followups as known
from research_questions import validate_research_questions


class KnownKeyFollowups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = known.ROOT / 'experiments/records/lp2-known-vigenere-keys/record.json'
        cls.record = json.loads(cls.path.read_bytes())
        cls.recipes = {r['id']: r for r in cls.record['browser_followups']}
        cls.language = cls.recipes['known-keys-language-comparison']
        cls.words = cls.recipes['known-keys-word-reset-language']

    def test_deterministic_generator_executes_only_synthetic_controls(self):
        original = fixed.runner.run
        executed = []
        def synthetic_only(task):
            self.assertEqual([p['id'] for p in task['pages']], ['lp1-01'])
            self.assertIn('synthetic', task['title'].lower())
            self.assertEqual(len(task['criterion']['values']), 184)
            executed.append(task['taskId'])
            return original(task)
        before = self.path.read_bytes()
        with patch.object(fixed.runner, 'run', side_effect=synthetic_only):
            self.assertEqual(known.build(), self.record)
        self.assertTrue(executed)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertLess(len(before), 512 * 1024)

    def test_exact_original_programs_and_input_pins(self):
        index = json.loads((known.ROOT / 'data/published-program-source-index.json').read_bytes())
        expanded = finite.compile_card(self.language['card'])
        self.assertEqual(expanded['declaration']['programCount'], 42)
        self.assertEqual(expanded['declaration']['caseCount'], 2352)
        programs = {fixed.digest(e['steps']) for e in index['entries']}
        self.assertEqual(programs, {fixed.digest(v['compiled']['steps']) for v in expanded['variants']})
        for recipe in (self.language, self.words):
            authored.validate_recipe(recipe, known.ROOT, set(self.record['scope']['pages']))
            self.assertEqual(len(recipe['control']['members']), 42)
            self.assertEqual(recipe['inputs']['pages'][50]['id'], 'lp2-50')
            self.assertEqual(recipe['card']['rules']['evaluation']['value'], fixed.LANGUAGE_CRITERION)

    def test_word_extension_changes_exactly_one_rule(self):
        expected = copy.deepcopy(self.language['card'])
        expected['method']['value']['operations'][0]['reset'] = 'word'
        self.assertEqual(expected, self.words['card'])
        self.assertEqual(self.language['inputs'], self.words['inputs'])
        original = finite.compile_card(self.language['card'])['variants']
        changed = finite.compile_card(self.words['card'])['variants']
        for old, new in zip(original, changed):
            self.assertEqual(old['settings'], new['settings'])
            steps = copy.deepcopy(old['compiled']['steps'])
            steps[0]['reset'] = 'word'
            self.assertEqual(steps, new['compiled']['steps'])

    def test_fixed_recipe_and_historical_findings_unchanged_and_questions_open(self):
        self.assertIn('second-koan-word-reset-warning', self.recipes)
        self.assertNotIn('kind', self.recipes['second-koan-word-reset-warning'])
        self.assertEqual(self.record['research_questions'], known.questions())
        validate_research_questions(self.record['research_questions'], self.record)
        self.assertTrue(all(q['state'] == 'open' for q in self.record['research_questions']))
        self.assertIn('2352', self.record['summary'])
        self.assertIn('None matched', self.record['summary'])
        self.assertIn('not a recovered reading', self.language['limitation'])
        self.assertIn('not a translation', self.words['limitation'])
        self.assertIn('each non-rune mark ends a word', self.words['limitation'])


if __name__ == '__main__':
    unittest.main()
