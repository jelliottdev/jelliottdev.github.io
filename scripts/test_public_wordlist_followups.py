"""Detached wordlist adapter: source audits and synthetic witnesses, never target runs."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import browser_followups as fixed
import finite_control_storage as storage
import finite_followup_cards as finite
import public_wordlist_followups as wordlist


class PublicWordlistFollowups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = wordlist.ROOT / wordlist.BASE
        cls.before = {p: p.read_bytes() for p in cls.folder.iterdir() if p.is_file()}
        cls.original = json.loads(cls.before[cls.folder / 'record.json'])
        cls.controls = set()
        run = fixed.runner.run
        def synthetic_only(task):
            if [p['id'] for p in task['pages']] != ['lp1-01'] or 'synthetic' not in task['title'].lower():
                raise AssertionError('manuscript target execution forbidden')
            if task['criterion']['kind'] != 'exact-prefix' or len(task['criterion']['values']) != 184:
                raise AssertionError('full synthetic Warning output required')
            cls.controls.add(task['taskId'])
            return run(task)
        with patch.object(fixed.runner, 'run', side_effect=synthetic_only), patch('subprocess.run', side_effect=AssertionError('archived source execution forbidden')):
            cls.declared = wordlist.source()
            cls.proposal = wordlist.proposed()
        cls.recipe = next(r for r in cls.proposal['browser_followups'] if r['id'] == wordlist.IDENTIFIER)

    def test_scientific_fields_and_every_source_file_remain_exactly_unchanged(self):
        self.assertEqual(len(self.controls), 43)
        for name, value in self.original.items():
            if name in ('browser_followups', 'research_questions'):
                self.assertEqual(self.proposal[name][:len(value)], value)
            else:
                self.assertEqual(self.proposal[name], value)
        self.assertEqual({p: p.read_bytes() for p in self.before}, self.before)
        self.assertEqual(self.proposal['research_questions'][-1], wordlist.questions()[0])
        self.assertNotIn('results', self.recipe)

    def test_complete_source_keys_nine_openings_phase_zero_subtraction_and_page_only_scope(self):
        plan = json.loads((self.folder / 'plan.json').read_bytes())
        opening = json.loads((wordlist.ROOT / wordlist.OPENING_PLAN).read_bytes())
        lookup = {r: n for n, r in enumerate(wordlist.RUNES)}
        keys = [[lookup[r] for r in k['runes']] for k in plan['keys']]
        self.assertEqual([k['indices'] for k in self.declared['keys']], keys)
        self.assertEqual([k['runes'] for k in self.declared['keys']], [k['runes'] for k in plan['keys']])
        card = self.recipe['card']
        self.assertLessEqual(len(json.dumps(card, ensure_ascii=False, separators=(',', ':')).encode()), 12000)
        self.assertEqual(card['method']['value']['operations'], [{'id': 'repeating_key', 'direction': 'subtract', 'reset': 'page'}])
        self.assertEqual(card['rules']['evaluation']['value'], {'kind': 'exact-prefix-set', 'openings': [{'id': o['id'], 'values': o['indices']} for o in opening['openings']]})
        self.assertEqual(card['scope']['value']['pages'], wordlist.PAGES)
        expanded = finite.compile_card(card)
        self.assertEqual(expanded['declaration']['programCount'], 43)
        self.assertEqual(expanded['declaration']['caseCount'], 2408)
        self.assertEqual({tuple(v['compiled']['steps'][0]['key']) for v in expanded['variants']}, {tuple(k) for k in keys})
        for v in expanded['variants']:
            self.assertEqual(v['compiled']['steps'], [{'op': 'keyed-shift', 'key': v['compiled']['steps'][0]['key'], 'mode': 'repeat', 'direction': 'subtract', 'reset': 'page'}])
            self.assertEqual(v['compiled']['pages'], wordlist.PAGES)
        self.assertEqual(len(storage.expand(self.recipe['control'])['members']), 43)

    def test_saved_prefix_inverse_audit_and_certificate_limits_make_no_full_output_or_zip_claim(self):
        audit = self.declared['audit']
        self.assertEqual(audit['declaredCases'], 2408)
        self.assertEqual(audit['runeBearingCases'], 2365)
        self.assertEqual(audit['emptyCases'], 43)
        self.assertEqual(audit['openingComparisons'], 21285)
        self.assertEqual(audit['savedPrefixRunesVerified'], 2365 * 9)
        self.assertEqual(audit['completeSourceOutputsVerifiedHere'], 0)
        self.assertFalse(audit['sourceArchiveInspectedHere'])
        self.assertIn('not complete outputs', audit['certificateMeaning'])
        self.assertIn('excluded from opening comparisons', self.recipe['scope_change'])
        self.assertIn('new browser replay has no results yet', self.recipe['limitation'])
        self.assertIn('does not verify the separate 58-page ZIP', self.recipe['limitation'])
        for pin in self.recipe['inputs']['pages']:
            self.assertEqual(pin['text_sha256'], hashlib.sha256((wordlist.ROOT / 'text' / (pin['id'] + '.txt')).read_bytes()).hexdigest())
        self.assertEqual(len(self.recipe['inputs']['pages']), 56)

    def test_pinned_sources_and_freshly_repinned_invalid_results_or_certificate_fail_closed(self):
        read = Path.read_bytes
        for name in wordlist.PINS:
            target = self.folder / name
            def altered(path, *, target=target):
                return b'changed source' if path.resolve() == target.resolve() else read(path)
            with self.subTest(name=name), patch.object(Path, 'read_bytes', altered), self.assertRaisesRegex(ValueError, 'source pin changed'):
                wordlist.source()
        for name, mutate, message in [
            ('results.json', lambda v: v['cases'][0].__setitem__('first_nine_runes', 'ᚠ' * 9), 'inverse arithmetic'),
            ('results.json', lambda v: v['cases'][0].__setitem__('opening_matches', ['warning']), 'opening decision'),
            ('results.json', lambda v: v['cases'].pop(), 'case domain'),
            ('results.json', lambda v: v.__setitem__('opening_comparisons', 2408 * 9), 'coverage total'),
            ('source-output-certificate.json', lambda v: v.__setitem__('page_files', 56), 'certificate limits'),
            ('source-output-certificate.json', lambda v: v.__setitem__('complete_matches', 2408), 'certificate limits'),
        ]:
            target = self.folder / name
            value = json.loads(read(target))
            mutate(value)
            raw = json.dumps(value, ensure_ascii=False).encode('utf-8')
            pins = {**wordlist.PINS, name: hashlib.sha256(raw).hexdigest()}
            def altered(path, *, target=target, raw=raw):
                return raw if path.resolve() == target.resolve() else read(path)
            with self.subTest(name=name, message=message), patch.dict(wordlist.PINS, pins), patch.object(Path, 'read_bytes', altered), self.assertRaisesRegex(ValueError, message):
                wordlist.source()

    def test_source_audit_is_required_owned_drift_refused_and_later_unrelated_items_preserved(self):
        with patch.object(wordlist, 'source', side_effect=ValueError('audit failed')), self.assertRaisesRegex(ValueError, 'audit failed'):
            wordlist.proposed()
        installed = copy.deepcopy(self.proposal)
        installed['browser_followups'].append({'id': 'later-unrelated', 'sentinel': True})
        installed['research_questions'].append({'id': 'later-unrelated', 'state': 'open', 'note': 'Another check.', 'question': 'Does another fixed rule change the result?', 'records': []})
        with patch.object(wordlist, 'source', return_value={'record': installed}), patch.object(wordlist, 'candidate', return_value=copy.deepcopy(self.recipe)):
            self.assertEqual(wordlist.proposed(), installed)
        installed['browser_followups'][0]['motivation'] = 'Changed owned check.'
        with patch.object(wordlist, 'source', return_value={'record': installed}), patch.object(wordlist, 'candidate', return_value=copy.deepcopy(self.recipe)), self.assertRaisesRegex(ValueError, 'recipe changed'):
            wordlist.proposed()

    def test_real_browser_source_admission_validates43_full_controls_and2408_unrun_cases(self):
        payload = {'record': self.proposal, 'bundle': json.loads((wordlist.ROOT / 'data/local-run-inputs.json').read_bytes())}
        code = r"""const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto'),E=require('./local-experiment.js'),A=require('./authored-finite-followup.js'),input=JSON.parse(fs.readFileSync(0,'utf8')),run=E.run,hash=v=>crypto.createHash('sha256').update(v).digest('hex');let controls=0;E.run=task=>{assert.deepEqual(task.pages.map(p=>p.id),['lp1-01']);assert(task.title.toLowerCase().includes('synthetic'));assert.equal(task.criterion.values.length,184);controls++;return run(task);};(async()=>{const bytes=Buffer.from(JSON.stringify(input.record)),recipe=input.record.browser_followups.find(r=>r.id==='public-wordlist-nine-openings'),origin={recordId:input.record.id,followupId:recipe.id,recordSha256:hash(bytes),protocolSha256:hash(E.stable(recipe))},plan=await A.fromSource(origin,{sourceBytes:bytes,bundle:input.bundle,crypto:crypto.webcrypto});assert.equal(plan.domain.programs,43);assert.equal(plan.domain.pages,56);assert.equal(plan.domain.totalCases,2408);console.log(JSON.stringify({controls,cases:plan.domain.totalCases}));})().catch(e=>{console.error(e);process.exitCode=1;});"""
        result = subprocess.run(['node', '-e', code], input=json.dumps(payload, ensure_ascii=True), cwd=wordlist.ROOT, text=True, encoding='utf-8', capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), {'controls': 43, 'cases': 2408})

    def test_cli_check_is_detached_and_output_cannot_escape_private_qa(self):
        with patch.object(sys, 'argv', ['tool', '--output', str(wordlist.ROOT / 'experiments')]), self.assertRaisesRegex(ValueError, 'outer qa-temp'):
            wordlist.main()
        output = io.StringIO()
        with patch.object(wordlist, 'proposed', return_value=copy.deepcopy(self.proposal)), patch.object(sys, 'argv', ['tool', '--check']), contextlib.redirect_stdout(output), patch.object(Path, 'write_text', side_effect=AssertionError('check must not write')), patch.object(Path, 'write_bytes', side_effect=AssertionError('check must not write')):
            wordlist.main()
        summary = json.loads(output.getvalue())
        self.assertFalse(summary['installed'])
        self.assertFalse(summary['detachedOutputWritten'])
        self.assertEqual(summary['targetExecutions'], 0)
        self.assertEqual({p: p.read_bytes() for p in self.before}, self.before)

if __name__ == '__main__':
    unittest.main()
