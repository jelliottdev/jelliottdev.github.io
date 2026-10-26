"""Exact named folding replays, with source immutability and synthetic-only gates."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import browser_followups as fixed
import build_repeating_key_banks as banks
import finite_control_storage as storage
import finite_followup_cards as finite
import folded_key_followups as folded


class FoldedKeyFollowups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = folded.ROOT / folded.BASE / 'record.json'
        cls.original_bytes = cls.path.read_bytes()
        cls.original = json.loads(cls.original_bytes)
        cls.executed = set()
        run = fixed.runner.run
        def synthetic_only(task):
            if [p['id'] for p in task['pages']] != ['lp1-01'] or 'synthetic' not in task['title'].lower():
                raise AssertionError('manuscript target execution forbidden')
            if task['criterion']['kind'] != 'exact-prefix' or len(task['criterion']['values']) != 184:
                raise AssertionError('complete 184-rune Warning control required')
            cls.executed.add(task['taskId'])
            return run(task)
        with patch.object(fixed.runner, 'run', side_effect=synthetic_only), patch('subprocess.run', side_effect=AssertionError('source program execution forbidden')):
            cls.declared = folded.source()
            cls.before = {p['path']: (folded.ROOT / p['path']).read_bytes() for p in cls.declared['pins']}
            cls.proposal = folded.proposed()
        cls.recipes = {r['id']: r for r in cls.proposal['browser_followups'] if r['id'] in [value[0] for value in folded.VARIANTS.values()]}

    def test_scientific_record_source_files_and_findings_remain_unchanged(self):
        for key, value in self.original.items():
            if key in ('browser_followups', 'research_questions'):
                self.assertEqual(self.proposal[key][:len(value)], value)
            else:
                self.assertEqual(self.proposal[key], value)
        self.assertEqual(self.path.read_bytes(), self.original_bytes)
        self.assertEqual({p: (folded.ROOT / p).read_bytes() for p in self.before}, self.before)
        self.assertEqual(self.declared['audit']['targetExecutions'], 0)
        self.assertEqual(self.declared['audit']['importedHistoricalReceipts'], 0)
        self.assertEqual(self.declared['audit']['caseDigest'], folded.CASE_DIGEST)
        self.assertEqual(self.proposal['finding'], self.original['finding'])
        self.assertEqual(self.proposal['outcome'], self.original['outcome'])

    def test_both_complete_named_variants_have_exact_domain_scope_and_same_nine_openings(self):
        total = 0
        for variant, (identifier, count) in folded.VARIANTS.items():
            recipe = self.recipes[identifier]
            card = recipe['card']
            self.assertEqual(card['method']['value']['operations'], [{'id': 'repeating_key', 'direction': 'subtract', 'reset': 'page'}])
            self.assertEqual(card['scope']['value']['pages'], folded.PAGES)
            self.assertEqual(len(folded.PAGES), 55)
            self.assertNotIn('lp2-50', folded.PAGES)
            self.assertEqual(card['rules']['evaluation']['value'], self.declared['criterion'])
            self.assertEqual(len(self.declared['criterion']['openings']), 9)
            self.assertTrue(all(len(o['values']) == 12 for o in self.declared['criterion']['openings']))
            parameters = card['rules']['searchBounds']['value']['parameters']
            self.assertEqual(len(parameters), 1)
            self.assertEqual(parameters[0]['name'], 'key')
            reference = parameters[0]['valuesFrom']
            self.assertEqual(reference['start'], 0)
            self.assertEqual(reference['count'], count)
            self.assertEqual(reference['bankId'], 'public-wordlist-' + variant + '-v1')
            domain = finite.compile_card(card)
            self.assertEqual(domain['declaration']['programCount'], count)
            self.assertEqual(domain['declaration']['caseCount'], count * 55)
            controls = storage.expand(recipe['control'])['members']
            self.assertEqual(len(controls), count)
            self.assertEqual([m['settings'] for m in controls], [v['settings'] for v in domain['variants']])
            self.assertEqual([m['control']['task']['steps'][0]['key'] for m in controls], banks.resolve(reference))
            total += count
        self.assertEqual(total, 1150)
        self.assertEqual(self.declared['audit']['historicalSettings'], 6272)
        self.assertEqual(self.declared['audit']['outsideBrowserSettings'], 5122)
        self.assertEqual(self.declared['audit']['unsupportedPeriod324Settings'], 648)

    def test_literal_examples_full_cycles_and_every_starting_place(self):
        repeat, named = folded.folded_vectors([[0, 1, 2]], 'fold-repeat-endpoints')
        self.assertEqual(named, 6)
        self.assertIn((0, 1, 2, 2, 1, 0), repeat)
        skipped, named = folded.folded_vectors([[0, 1, 2]], 'fold-skip-endpoints')
        self.assertEqual(named, 4)
        self.assertIn((0, 1, 2, 1), skipped)
        self.assertIn('ABCCBA', self.recipes[folded.VARIANTS['fold-repeat-endpoints'][0]]['motivation'])
        self.assertIn('ABCB', self.recipes[folded.VARIANTS['fold-skip-endpoints'][0]]['motivation'])

    def test_all_full_synthetic_controls_and_both_source_byte_forms_fit_unchanged_limits(self):
        expected = set()
        for recipe in self.recipes.values():
            self.assertEqual(recipe['control']['kind'], 'finite-program-controls-pooled-v1')
            legacy = storage.expand(recipe['control'])
            self.assertLessEqual(len(storage.stable(legacy).encode()), 2 * 1024 * 1024)
            for member in legacy['members']:
                control = member['control']
                task = control['task']
                expected.add(task['taskId'])
                self.assertEqual([p['id'] for p in task['pages']], ['lp1-01'])
                self.assertEqual(len(task['criterion']['values']), 184)
                self.assertEqual(task['criterion']['kind'], 'exact-prefix')
                self.assertEqual(len(control['expected_result_sha256']), 64)
                self.assertEqual(task['steps'][0]['direction'], 'subtract')
                self.assertEqual(task['steps'][0]['reset'], 'page')
        self.assertEqual(self.executed, expected)
        self.assertEqual(len(expected), 1150)
        self.assertLessEqual(len(json.dumps(self.proposal, ensure_ascii=False, separators=(',', ':')).encode()) + 1, 2 * 1024 * 1024)
        self.assertLessEqual(len(json.dumps(self.proposal, ensure_ascii=False, indent=2).encode()) + 1, 2 * 1024 * 1024)

    def test_pin_and_bank_tampering_cannot_produce_partial_or_relabelled_replays(self):
        original = Path.read_bytes
        for target in [folded.BASE + '/run.py', folded.BASE + '/results.json', 'experiments/suites/classical-key-schedules/manifest.json', 'experiments/suites/classical-key-schedules/engine.py']:
            def altered(path, chosen=target):
                raw = original(path)
                return raw + b' ' if path.resolve() == (folded.ROOT / chosen).resolve() else raw
            with patch.object(Path, 'read_bytes', altered), self.assertRaisesRegex(ValueError, 'pin changed'):
                folded.source()
        resolve = banks.resolve
        def wrong_vector(reference):
            keys = resolve(reference)
            keys[0][0] = (keys[0][0] + 1) % 29
            return keys
        with patch.object(banks, 'resolve', side_effect=wrong_vector), self.assertRaisesRegex(ValueError, 'bank differs'):
            folded.source()
        with self.assertRaisesRegex(ValueError, 'unknown folded'):
            folded.candidate(variant='rotate-left', declared=self.declared)
        for change in ('scope', 'criterion'):
            bad = copy.deepcopy(self.declared)
            if change == 'scope':
                bad['variants']['fold-repeat-endpoints']['reference']['count'] = 1
            else:
                bad['criterion']['openings'][0]['values'][0] = (bad['criterion']['openings'][0]['values'][0] + 1) % 29
            with self.assertRaisesRegex(ValueError, 'complete audited|historical opening'):
                folded.candidate(variant='fold-repeat-endpoints', declared=bad)

    def test_proposal_is_idempotent_and_questions_do_not_claim_browser_findings(self):
        declared = copy.deepcopy(self.declared)
        declared['record'] = copy.deepcopy(self.proposal)
        with patch.object(folded, 'source', return_value=declared), patch.object(folded, 'candidate', side_effect=lambda root, variant, declared=None: copy.deepcopy(self.recipes[folded.VARIANTS[variant][0]])):
            self.assertEqual(folded.proposed(), self.proposal)
        for question in folded.questions():
            self.assertEqual(question['state'], 'open')
            self.assertEqual(question['records'], [])
            self.assertIn('not imported', question['note'])
        for recipe in self.recipes.values():
            self.assertNotIn('results', recipe)
            self.assertIn('no saved results yet', recipe['limitation'])
            self.assertIn('other folding variant', recipe['limitation'])


if __name__ == '__main__':
    unittest.main()
