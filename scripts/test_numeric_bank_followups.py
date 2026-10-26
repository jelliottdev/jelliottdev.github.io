"""Detached numerical-bank declarations preserve sources and execute controls only."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import subprocess
import unittest
from unittest.mock import patch

import authored_finite_followups as authored
import browser_boundary_variations as boundary
import browser_followups as fixed
import finite_control_storage as storage
import finite_followup_cards as finite
import numeric_bank_followups as numeric
from research_questions import validate_research_questions


class NumericBankFollowups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = {rid: numeric.ROOT / 'experiments/records' / rid / 'record.json' for rid in numeric.FAMILIES}
        cls.before = {rid: path.read_bytes() for rid, path in cls.paths.items()}
        cls.original = {rid: json.loads(raw) for rid, raw in cls.before.items()}
        cls.executed = set()
        original_run = fixed.runner.run
        def synthetic_only(task):
            if [p['id'] for p in task['pages']] != ['lp1-01'] or 'synthetic' not in task['title'].lower():
                raise AssertionError('generator attempted a manuscript target')
            if task['criterion']['kind'] != 'exact-prefix' or len(task['criterion']['values']) != 184:
                raise AssertionError('control must check the complete Warning passage')
            cls.executed.add(task['taskId'])
            return original_run(task)
        with patch.object(fixed.runner, 'run', side_effect=synthetic_only), patch('subprocess.run', side_effect=AssertionError('source programs cannot execute')):
            cls.values = {rid: numeric.proposed(rid) for rid in numeric.FAMILIES}

    def test_all_four_detached_proposals_preserve_every_original_value_and_file(self):
        self.assertEqual(len(self.executed), 4 * 174)
        for rid, value in self.values.items():
            with self.subTest(record=rid):
                self.assertEqual(self.paths[rid].read_bytes(), self.before[rid])
                restored = copy.deepcopy(value)
                for field in ('browser_followups', 'research_questions'):
                    if field in self.original[rid]:
                        restored[field] = self.original[rid][field]
                    else:
                        del restored[field]
                self.assertEqual(restored, self.original[rid])
                self.assertEqual([r for r in value['browser_followups'] if r['id'] != numeric.identifier(rid)], [r for r in self.original[rid].get('browser_followups', []) if r['id'] != numeric.identifier(rid)])
                self.assertEqual([q for q in value['research_questions'] if q['id'] != numeric.identifier(rid)], [q for q in self.original[rid].get('research_questions', []) if q['id'] != numeric.identifier(rid)])
                self.assertEqual(value['finding'], self.original[rid]['finding'])
                self.assertEqual(value['outcome'], self.original[rid]['outcome'])
                self.assertLess(len(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()), 2 * 1024 * 1024)
                value['summary'] = 'detached test mutation'
                self.assertEqual(self.paths[rid].read_bytes(), self.before[rid])
                value['summary'] = self.original[rid]['summary']

    def test_exact_compact_bank_identity_174_settings_9744_cases_and_no_literal_key_axis(self):
        for rid, value in self.values.items():
            with self.subTest(record=rid):
                recipe, family = next(r for r in value['browser_followups'] if r['id'] == numeric.identifier(rid)), numeric.FAMILIES[rid]
                card = recipe['card']
                self.assertLessEqual(len(json.dumps(card, ensure_ascii=False, separators=(',', ':')).encode()), 12 * 1024)
                self.assertEqual(card['method']['value']['operations'], [{'id': 'finite_key_bank', 'bankId': family['bankId'], 'bankSha256': family['bankSha256']}])
                self.assertEqual(card['scope']['value']['pages'], numeric.PAGES)
                axes = card['rules']['searchBounds']['value']['parameters']
                self.assertEqual({axis['name'] for axis in axes}, {'offset', 'direction', 'reset'})
                self.assertEqual(next(a['values'] for a in axes if a['name'] == 'offset'), list(range(29)))
                expanded = finite.compile_card(card)
                self.assertEqual(expanded['declaration']['programCount'], 174)
                self.assertEqual(expanded['declaration']['caseCount'], 9744)
                actual = {(next(s['value'] for s in v['settings'] if s['name'] == 'offset'), v['compiled']['steps'][0]['direction'], v['compiled']['steps'][0]['reset']) for v in expanded['variants']}
                self.assertEqual(actual, {(offset, direction, reset) for offset in range(29) for direction in ('subtract', 'add') for reset in ('page', 'line', 'word')})
                self.assertTrue(all(len(v['compiled']['steps']) == 1 and v['compiled']['steps'][0]['op'] == 'finite-shift' for v in expanded['variants']))
                self.assertEqual(card['rules']['evaluation']['value'], fixed.LANGUAGE_CRITERION)
                controls = storage.expand(recipe['control'])['members']
                self.assertEqual(len(controls), 174)
                self.assertTrue(all(len(m['control']['task']['criterion']['values']) == 184 for m in controls))

    def test_independent_historical_audits_cover_every_archived_array_and_original_opening_decision(self):
        beginnings = {'prime-minus-one-v1': [1, 2, 4, 6, 10, 12], 'prime-v1': [2, 3, 5, 7, 11, 13],
                      'fibonacci-v1': [0, 1, 1, 2, 3, 5], 'totient-v1': [1, 1, 2, 2, 4, 2]}
        for rid, family in numeric.FAMILIES.items():
            with self.subTest(record=rid):
                declared = numeric.source(rid)
                self.assertEqual(declared['audit'], {'historicalCases': 3190, 'historicalComparisons': 28710,
                    'historicalMatchingCases': 0, 'historicalOutputIndices': 751448})
                self.assertEqual(numeric.independent_terms(family['bankId'], 6), beginnings[family['bankId']])
                pins = {p['path']: p['sha256'] for p in declared['pins']}
                for name, sha in family['pins'].items():
                    self.assertEqual(pins['experiments/records/' + rid + '/' + name], sha)
                for item in self.original[rid]['reproduction']['inputs']:
                    self.assertEqual(pins[item['path']], item['sha256'])

    def test_shared_boundary_family_receives_fixed_page_base_and_only_explicit_restart_extension(self):
        rid = 'lp2-prime-openings'
        with patch.object(numeric.boundary, 'family', wraps=boundary.family) as shared, patch.object(authored, 'construct_followup', side_effect=lambda root, **kwargs: kwargs):
            result = numeric.candidate(rid, declared={'unused': True})
        self.assertEqual(shared.call_count, 1)
        base = shared.call_args.args[0]
        self.assertEqual(shared.call_args.kwargs, {'operation_index': 0, 'allowed_resets': ['page', 'line', 'word']})
        self.assertEqual(base['method']['value']['operations'][0]['reset'], 'page')
        self.assertEqual({a['name'] for a in base['rules']['searchBounds']['value']['parameters']}, {'offset', 'direction'})
        self.assertNotIn('reset', result['card']['method']['value']['operations'][0])

    def test_raw_input_pins_empty_page_and_reference_only_questions_are_honest(self):
        for rid, value in self.values.items():
            recipe = next(r for r in value['browser_followups'] if r['id'] == numeric.identifier(rid))
            self.assertEqual(len(recipe['inputs']['pages']), 56)
            for pin in recipe['inputs']['pages']:
                self.assertEqual(pin['text_sha256'], hashlib.sha256((numeric.ROOT / 'text' / (pin['id'] + '.txt')).read_bytes()).hexdigest())
            q = next(q for q in value['research_questions'] if q['id'] == numeric.identifier(rid))
            self.assertEqual(q, numeric.questions(rid)[0])
            self.assertEqual(q['state'], 'open')
            self.assertNotIn('question', q)
            validate_research_questions(value['research_questions'], value, strict_authoring=True)
            self.assertIn('nine fixed historical openings', recipe['scope_change'])
            self.assertIn('305-term sequence', recipe['limitation'])
            self.assertIn('without wrapping, skipped runes or carry between pages', recipe['limitation'])
            self.assertIn('29 starting places', recipe['motivation'])
        fibonacci = next(r for r in self.values['lp2-fibonacci-openings']['browser_followups'] if r['id'] == numeric.identifier('lp2-fibonacci-openings'))
        self.assertIn('14 terms', fibonacci['scope_change'])
        self.assertIn('duplicates, not independent trials', fibonacci['limitation'])

    def test_source_mutation_bank_drift_and_independent_output_tamper_fail_closed(self):
        rid = 'lp2-prime-openings'
        original_read = Path.read_bytes
        targets = [('experiments/records/' + rid + '/run.py', lambda raw: raw + b' '),
                   ('text/lp2-00.txt', lambda raw: raw + b' '),
                   ('experiments/records/' + rid + '/record.json', lambda raw: json.dumps({**json.loads(raw), 'id': 'wrong-owner'}).encode())]
        for name, mutate in targets:
            def changed(path):
                raw = original_read(path)
                return mutate(raw) if path == numeric.ROOT / name else raw
            with self.subTest(path=name), patch.object(Path, 'read_bytes', changed), self.assertRaises(ValueError):
                numeric.source(rid)
        bank = numeric.banks.get(numeric.FAMILIES[rid]['bankId'], numeric.FAMILIES[rid]['bankSha256'])
        bank['values'][0] = (bank['values'][0] + 1) % 29
        with patch.object(numeric.banks, 'get', return_value=bank), self.assertRaises(ValueError):
            numeric.source(rid)
        path = numeric.ROOT / 'experiments/records' / rid / 'results.json'
        result = json.loads(original_read(path))
        result['cases'][0]['output_indices'][0] = (result['cases'][0]['output_indices'][0] + 1) % 29
        raw = json.dumps(result).encode()
        families = copy.deepcopy(numeric.FAMILIES)
        families[rid]['pins']['results.json'] = numeric.digest(raw)
        def changed_result(target):
            return raw if target == path else original_read(target)
        with patch.object(numeric, 'FAMILIES', families), patch.object(Path, 'read_bytes', changed_result), self.assertRaisesRegex(ValueError, 'inverse arithmetic'):
            numeric.source(rid)

    def test_actual_browser_source_admission_replays_all_696_complete_synthetic_controls_only(self):
        payload = {'records': list(self.values.values()), 'bundle': json.loads((numeric.ROOT / 'data/local-run-inputs.json').read_bytes())}
        code = r"""const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto'),E=require('./local-experiment.js'),A=require('./authored-finite-followup.js'),input=JSON.parse(fs.readFileSync(0,'utf8')),run=E.run,hash=v=>crypto.createHash('sha256').update(v).digest('hex');let controls=0;E.run=task=>{assert.deepEqual(task.pages.map(p=>p.id),['lp1-01']);assert(task.title.toLowerCase().includes('synthetic'));assert.equal(task.criterion.values.length,184);controls++;return run(task);};(async()=>{let cases=0;for(const record of input.records){const bytes=Buffer.from(JSON.stringify(record)),recipe=record.browser_followups.find(r=>r.id.endsWith('-stream-reset-language')),origin={recordId:record.id,followupId:recipe.id,recordSha256:hash(bytes),protocolSha256:hash(E.stable(recipe))},plan=await A.fromSource(origin,{sourceBytes:bytes,bundle:input.bundle,crypto:crypto.webcrypto});assert.equal(plan.domain.programs,174);assert.equal(plan.domain.pages,56);assert.equal(plan.domain.totalCases,9744);cases+=plan.domain.totalCases;}console.log(JSON.stringify({controls,cases}));})().catch(error=>{console.error(error);process.exitCode=1;});"""
        completed = subprocess.run(['node', '-e', code], input=json.dumps(payload, ensure_ascii=True), cwd=numeric.ROOT,
                                   text=True, encoding='utf-8', capture_output=True, check=True)
        self.assertEqual(json.loads(completed.stdout), {'controls': 696, 'cases': 38976})

    def test_already_installed_identical_proposal_is_idempotent_and_changed_owned_recipe_rejected(self):
        rid = 'lp2-prime-openings'
        expected = self.values[rid]
        declared = {'record': copy.deepcopy(expected)}
        with patch.object(numeric, 'source', return_value=declared), patch.object(numeric, 'candidate', return_value=copy.deepcopy(next(r for r in expected['browser_followups'] if r['id'] == numeric.identifier(rid)))):
            self.assertEqual(numeric.proposed(rid), expected)
        next(r for r in declared['record']['browser_followups'] if r['id'] == numeric.identifier(rid))['motivation'] = 'Changed authored purpose.'
        with patch.object(numeric, 'source', return_value=declared), patch.object(numeric, 'candidate', return_value=copy.deepcopy(next(r for r in expected['browser_followups'] if r['id'] == numeric.identifier(rid)))), self.assertRaisesRegex(ValueError, 'existing numerical-bank recipe changed'):
            numeric.proposed(rid)

    def test_existing_recipe_and_question_keep_position_after_unrelated_addition(self):
        rid = 'lp2-prime-openings'
        expected = copy.deepcopy(self.values[rid])
        expected['browser_followups'].append({'id': 'unrelated-after', 'sentinel': 1})
        expected['research_questions'].append({'id': 'unrelated-after', 'state': 'open', 'note': 'Another question.', 'question': 'Does another bounded variation change the output?', 'records': []})
        recipe = next(r for r in expected['browser_followups'] if r['id'] == numeric.identifier(rid))
        with patch.object(numeric, 'source', return_value={'record': expected}), patch.object(numeric, 'candidate', return_value=recipe):
            self.assertEqual(numeric.proposed(rid), expected)

    def test_cli_can_only_write_detached_outer_qa_temp_and_check_reports_drift(self):
        minimal = {rid: copy.deepcopy(value) for rid, value in self.values.items()}
        with patch.object(numeric, 'proposed', side_effect=lambda rid: minimal[rid]), patch.object(sys, 'argv', ['numeric_bank_followups.py', '--output', str(numeric.ROOT / 'experiments')]), self.assertRaisesRegex(ValueError, 'outer qa-temp'):
            numeric.main()
        minimal[next(iter(minimal))]['summary'] += ' deliberate test drift'
        with patch.object(numeric, 'proposed', side_effect=lambda rid: minimal[rid]), patch.object(sys, 'argv', ['numeric_bank_followups.py', '--check']), self.assertRaisesRegex(ValueError, 'installed numerical-bank declarations differ'):
            numeric.main()


if __name__ == '__main__':
    unittest.main()
