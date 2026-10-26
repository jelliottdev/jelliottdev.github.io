"""Source-audited detached nine-opening proposals: synthetic controls only."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import browser_followups as fixed
import finite_control_storage as storage
import finite_followup_cards as finite
import numeric_bank_followups as numeric
import numeric_opening_set_followups as opening


class NumericOpeningSetFollowups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = {rid: (numeric.ROOT / 'experiments/records' / rid / 'record.json').read_bytes() for rid in numeric.FAMILIES}
        cls.original = {rid: json.loads(raw) for rid, raw in cls.before.items()}
        cls.controls = set()
        run = fixed.runner.run
        def synthetic_only(task):
            if [page['id'] for page in task['pages']] != ['lp1-01'] or 'synthetic' not in task['title'].lower():
                raise AssertionError('manuscript task forbidden')
            if task['criterion']['kind'] != 'exact-prefix' or len(task['criterion']['values']) != 184:
                raise AssertionError('complete synthetic Warning required')
            cls.controls.add(task['taskId'])
            return run(task)
        with patch.object(fixed.runner, 'run', side_effect=synthetic_only), patch('subprocess.run', side_effect=AssertionError('source execution forbidden')):
            cls.proposals = {rid: opening.proposed(rid) for rid in numeric.FAMILIES}

    def recipe(self, rid):
        return next(value for value in self.proposals[rid]['browser_followups'] if value['id'] == opening.identifier(rid))

    def test_all_four_proposals_preserve_original_values_files_order_and_findings(self):
        self.assertEqual(len(self.controls), 4 * 58)
        for rid, proposed in self.proposals.items():
            self.assertEqual((numeric.ROOT / 'experiments/records' / rid / 'record.json').read_bytes(), self.before[rid])
            for field, value in self.original[rid].items():
                if field in ('browser_followups', 'research_questions'):
                    self.assertEqual(proposed[field][:len(value)], value)
                else:
                    self.assertEqual(proposed[field], value)
            self.assertEqual(proposed['finding'], self.original[rid]['finding'])
            self.assertEqual(proposed['outcome'], self.original[rid]['outcome'])
            self.assertNotIn('results', self.recipe(rid))
            self.assertEqual(proposed['research_questions'][-1], opening.questions(rid)[0])

    def test_exact_nine_ordered_plan_prefixes_bank_pins_and_58_page_only_settings(self):
        expected_ids = ['warning', 'welcome', 'some-wisdom', 'first-koan', 'loss-of-divinity', 'second-koan', 'instruction', 'lp2-56', 'lp2-57']
        for rid, family in numeric.FAMILIES.items():
            recipe = self.recipe(rid)
            card = recipe['card']
            self.assertLessEqual(len(json.dumps(card, separators=(',', ':')).encode()), 12 * 1024)
            plan = json.loads((numeric.ROOT / 'experiments/records' / rid / 'plan.json').read_bytes())
            criterion = card['rules']['evaluation']['value']
            self.assertEqual(criterion, {'kind': 'exact-prefix-set', 'openings': [{'id': o['id'], 'values': o['indices']} for o in plan['openings']]})
            self.assertEqual([o['id'] for o in criterion['openings']], expected_ids)
            self.assertTrue(all(len(o['values']) == 12 for o in criterion['openings']))
            self.assertEqual(card['method']['value']['operations'], [{'id': 'finite_key_bank', 'bankId': family['bankId'], 'bankSha256': family['bankSha256'], 'reset': 'page'}])
            expansion = finite.compile_card(card)
            self.assertEqual(expansion['declaration']['programCount'], 58)
            self.assertEqual(expansion['declaration']['caseCount'], 3248)
            members = expansion['variants']
            settings = {(next(s['value'] for s in m['settings'] if s['name'] == 'offset'), m['compiled']['steps'][0]['direction']) for m in members}
            self.assertEqual(settings, {(o, d) for o in range(29) for d in ('subtract', 'add')})
            for member in members:
                step = member['compiled']['steps'][0]
                offset = next(s['value'] for s in member['settings'] if s['name'] == 'offset')
                self.assertEqual(step['reset'], 'page')
                self.assertEqual(step['key'], numeric.banks.resolve(family['bankId'], family['bankSha256'], offset))
                self.assertEqual(len(step['key']), 305-offset)
                self.assertEqual(member['compiled']['pages'], numeric.PAGES)
                self.assertEqual(member['compiled']['criterion'], criterion)
            self.assertEqual(len(storage.expand(recipe['control'])['members']), 58)

    def test_complete_inputs_empty_page_and_historical_case_counts_are_explained(self):
        for rid in numeric.FAMILIES:
            recipe = self.recipe(rid)
            self.assertEqual(len(recipe['inputs']['pages']), 56)
            for pin in recipe['inputs']['pages']:
                self.assertEqual(pin['text_sha256'], hashlib.sha256((numeric.ROOT / 'text' / (pin['id'] + '.txt')).read_bytes()).hexdigest())
            self.assertIn('rune-empty LP2-50 as no runes', recipe['scope_change'])
            self.assertIn('same nine ordered 12-rune openings', recipe['scope_change'])
            self.assertIn('3,248 declared page cases', recipe['limitation'])
            self.assertIn('3,190 rune-bearing cases', recipe['limitation'])
            self.assertIn('28,710 opening comparisons', recipe['limitation'])
            self.assertIn('new browser replay has no results yet', recipe['limitation'])
            self.assertIn('no wrap, skips or cross-page carry', recipe['limitation'])
        self.assertIn('duplicates, not independent trials', self.recipe('lp2-fibonacci-openings')['limitation'])

    def test_shared_full_source_audit_is_required_and_plan_drift_is_rejected(self):
        rid = 'lp2-prime-openings'
        with patch.object(numeric, 'source', side_effect=ValueError('audit failed')), self.assertRaisesRegex(ValueError, 'audit failed'):
            opening.proposed(rid)
        with patch.object(numeric, 'source', wraps=numeric.source) as audited:
            declared = numeric.source(rid)
            self.assertEqual(declared['audit']['historicalCases'], 3190)
            self.assertEqual(declared['audit']['historicalComparisons'], 28710)
        declared['pins'] = []
        with self.assertRaisesRegex(ValueError, 'audited opening plan changed'):
            opening.criterion(rid, declared=declared)

    def test_installed_equivalent_is_stable_with_unrelated_later_items_and_owned_drift_fails(self):
        rid = 'lp2-prime-openings'
        expected = copy.deepcopy(self.proposals[rid])
        expected['browser_followups'].append({'id': 'unrelated-later', 'sentinel': True})
        expected['research_questions'].append({'id': 'unrelated-later', 'state': 'open', 'note': 'Another inquiry.', 'question': 'Does another bounded variation change the output?', 'records': []})
        recipe = copy.deepcopy(self.recipe(rid))
        with patch.object(numeric, 'source', return_value={'record': expected}), patch.object(opening, 'candidate', return_value=recipe):
            self.assertEqual(opening.proposed(rid), expected)
        next(r for r in expected['browser_followups'] if r['id'] == opening.identifier(rid))['motivation'] = 'Changed.'
        with patch.object(numeric, 'source', return_value={'record': expected}), patch.object(opening, 'candidate', return_value=recipe), self.assertRaisesRegex(ValueError, 'opening-set recipe changed'):
            opening.proposed(rid)

    def test_browser_admission_compiles_232_controls_and_12992_unrun_cases(self):
        payload = {'records': list(self.proposals.values()), 'bundle': json.loads((numeric.ROOT / 'data/local-run-inputs.json').read_bytes())}
        code = r"""const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto'),E=require('./local-experiment.js'),A=require('./authored-finite-followup.js'),input=JSON.parse(fs.readFileSync(0,'utf8')),run=E.run,hash=v=>crypto.createHash('sha256').update(v).digest('hex');let controls=0;E.run=task=>{assert.deepEqual(task.pages.map(p=>p.id),['lp1-01']);assert(task.title.toLowerCase().includes('synthetic'));assert.equal(task.criterion.values.length,184);controls++;return run(task);};(async()=>{let cases=0;const domains=new Set();for(const record of input.records){const bytes=Buffer.from(JSON.stringify(record)),recipe=record.browser_followups.find(r=>r.id.endsWith('-stream-nine-openings')),origin={recordId:record.id,followupId:recipe.id,recordSha256:hash(bytes),protocolSha256:hash(E.stable(recipe))},plan=await A.fromSource(origin,{sourceBytes:bytes,bundle:input.bundle,crypto:crypto.webcrypto});assert.match(plan.domain.domainId,/^[a-f0-9]{64}$/);domains.add(plan.domain.domainId);assert.equal(plan.domain.programs,58);assert.equal(plan.domain.pages,56);assert.equal(plan.domain.totalCases,3248);cases+=plan.domain.totalCases;}assert.equal(domains.size,4);console.log(JSON.stringify({controls,cases}));})().catch(error=>{console.error(error);process.exitCode=1;});"""
        completed = subprocess.run(['node', '-e', code], input=json.dumps(payload, ensure_ascii=True), cwd=numeric.ROOT,
                                   text=True, encoding='utf-8', capture_output=True, check=True)
        self.assertEqual(json.loads(completed.stdout), {'controls': 232, 'cases': 12992})

    def test_cli_only_allows_detached_output_and_check_never_installs(self):
        with patch.object(sys, 'argv', ['tool', '--output', str(numeric.ROOT / 'experiments')]), self.assertRaisesRegex(ValueError, 'outer qa-temp'):
            opening.main()
        changed = copy.deepcopy(self.proposals)
        changed[next(iter(changed))]['summary'] += ' deliberate validation drift'
        with patch.object(opening, 'proposed', side_effect=lambda rid: changed[rid]), patch.object(sys, 'argv', ['tool', '--check', '--no-directwrite']), self.assertRaisesRegex(ValueError, 'installed numerical opening-set declarations differ'):
            opening.main()
        for rid, raw in self.before.items():
            self.assertEqual((numeric.ROOT / 'experiments/records' / rid / 'record.json').read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
