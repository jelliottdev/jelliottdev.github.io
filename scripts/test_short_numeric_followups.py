"""One exact nine-key family; all execution is synthetic, never manuscript work."""
import copy
import json
import subprocess
from pathlib import Path
import unittest
from unittest.mock import patch

import authored_finite_followups as authored
import browser_boundary_variations as boundary
import browser_followups as fixed
import finite_followup_cards as finite
import short_numeric_followups as short
from research_questions import validate_research_questions


class ShortNumericFollowups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = short.ROOT / short.BASE / 'record.json'
        cls.before = cls.path.read_bytes()
        cls.original = json.loads(cls.before)
        cls.executed = []
        original_run = fixed.runner.run
        def synthetic_only(task):
            if [p['id'] for p in task['pages']] != ['lp1-01'] or 'synthetic' not in task['title'].lower():
                raise AssertionError('generator attempted a manuscript target')
            if task['criterion']['kind'] != 'exact-prefix' or len(task['criterion']['values']) != 184:
                raise AssertionError('synthetic witness must compare every Warning rune')
            cls.executed.append(copy.deepcopy(task))
            return original_run(task)
        with patch.object(fixed.runner, 'run', side_effect=synthetic_only), patch('subprocess.run', side_effect=AssertionError('source programs cannot execute')):
            cls.value = short.proposed()
        cls.recipe = cls.value['browser_followups'][-1]

    def test_only_complete_synthetic_controls_and_detached_source_preservation(self):
        self.assertEqual(self.path.read_bytes(), self.before)
        self.assertTrue(self.executed)
        self.assertEqual(len({t['taskId'] for t in self.executed}), 54)
        unchanged = copy.deepcopy(self.value)
        for field in ('browser_followups', 'research_questions'):
            if field in self.original:
                unchanged[field] = self.original[field]
            else:
                del unchanged[field]
        self.assertEqual(unchanged, self.original)
        self.assertLess(len(json.dumps(self.value, ensure_ascii=False, separators=(',', ':')).encode()), 2 * 1024 * 1024)
        self.value['title'] = 'Detached mutation'
        self.assertEqual(self.path.read_bytes(), self.before)
        self.value['title'] = self.original['title']

    def test_all_nine_exact_source_keys_both_directions_and_all_restart_rules(self):
        declared = short.source()
        self.assertEqual([key['id'] for key in declared['keys']], ['mayan_fwd', 'mayan_rev', 'hash_bytes', 'hash_hexdigits',
            'cuneiform_17_13_55_1', 'cuneiform_rev', 'digits_1033', 'digits_3301', 'cuneiform+1033+3301'])
        self.assertEqual([len(key['indices']) for key in declared['keys']], [13, 13, 64, 128, 4, 4, 4, 4, 12])
        self.assertEqual(declared['keys'][0]['indices'], [10, 2, 14, 7, 19, 6, 18, 12, 7, 8, 17, 0, 19])
        self.assertEqual(declared['keys'][1]['indices'], declared['keys'][0]['indices'][::-1])
        self.assertEqual(declared['keys'][4]['indices'], [17, 13, 26, 1])
        # Independently parse the pinned source literals rather than copying a
        # hand list from the candidate's expanded controls.
        source_dir = short.ROOT / short.BASE / 'source/analysis/campaign7'
        cuneiform = short.literal(source_dir / 'c2_cuneiform.py', 'KEYS')
        for name, values in cuneiform.items():
            self.assertEqual(next(k['indices'] for k in declared['keys'] if k['id'] == name), [n % 29 for n in values])
        hex_string = short.literal(source_dir / 'b4_hash_kdf.py', 'HEX')
        self.assertEqual(declared['keys'][2]['indices'], [n % 29 for n in bytes.fromhex(hex_string)])
        self.assertEqual(declared['keys'][3]['indices'], [int(c, 16) for c in hex_string])
        expanded = finite.compile_card(self.recipe['card'])
        self.assertEqual(expanded['declaration']['programCount'], 54)
        self.assertEqual(expanded['declaration']['caseCount'], 2970)
        actual = {(tuple(v['compiled']['steps'][0]['key']), v['compiled']['steps'][0]['direction'], v['compiled']['steps'][0]['reset']) for v in expanded['variants']}
        expected = {(tuple(k['indices']), direction, reset) for k in declared['keys'] for direction in ('subtract', 'add') for reset in ('page', 'line', 'word')}
        self.assertEqual(actual, expected)
        self.assertTrue(all(len(v['compiled']['steps']) == 1 and v['compiled']['steps'][0]['op'] == 'keyed-shift' for v in expanded['variants']))
        self.assertEqual(self.recipe['card']['scope']['value']['pages'], short.PAGES)
        self.assertEqual(len(short.PAGES), 55)
        self.assertNotIn('lp2-50', short.PAGES)
        self.assertEqual(self.recipe['card']['rules']['evaluation']['value'], fixed.LANGUAGE_CRITERION)

    def test_shared_boundary_helper_is_the_only_restart_family_construction(self):
        with patch.object(short.boundary, 'family', wraps=boundary.family) as shared:
            self.assertEqual(short.candidate(), self.recipe)
        self.assertEqual(shared.call_count, 1)
        baseline = shared.call_args.args[0]
        self.assertEqual(shared.call_args.kwargs, {'operation_index': 0, 'allowed_resets': ['page', 'line', 'word']})
        self.assertEqual(baseline['method']['value']['operations'][0]['reset'], 'page')
        self.assertEqual([a['name'] for a in baseline['rules']['searchBounds']['value']['parameters']], ['key', 'direction'])
        self.assertNotIn('reset', self.recipe['card']['method']['value']['operations'][0])

    def test_full_provenance_pins_raw_inputs_and_honest_open_question(self):
        pins = {p['path']: p['sha256'] for p in short.provenance()}
        for item in self.original['reproduction']['inputs']:
            self.assertEqual(pins[item['path']], item['sha256'])
        for name, sha in short.PINS.items():
            self.assertEqual(pins[short.BASE + '/' + name], sha)
        for pid in short.PAGES:
            text = (short.ROOT / 'text' / (pid + '.txt')).read_bytes()
            self.assertEqual(pins['text/' + pid + '.txt'], short.digest(text))
            self.assertEqual(next(p['text_sha256'] for p in self.recipe['inputs']['pages'] if p['id'] == pid), short.digest(text))
        q = self.value['research_questions'][-1]
        self.assertEqual(q, short.questions()[0])
        self.assertEqual(q['state'], 'open')
        self.assertNotIn('question', q)
        validate_research_questions(self.value['research_questions'], self.value, strict_authoring=True)
        self.assertIn('new runs, not reused archived outputs', self.recipe['limitation'])
        self.assertIn('No Atbash, F interruption, long derived keys, joined whole-book stream or other starting places', self.recipe['limitation'])
        self.assertIn('word restarts also happen at spaces and punctuation', self.recipe['limitation'])
        self.assertIn('earlier English score', self.recipe['motivation'])
        self.assertEqual(self.value['finding'], self.original['finding'])
        self.assertEqual(self.value['outcome'], self.original['outcome'])

    def test_source_ownership_source_hashes_and_official_raw_changes_fail_closed(self):
        original_read = Path.read_bytes
        cases = [(short.BASE + '/plan.json', lambda raw: raw + b' '),
                 (short.BASE + '/results.json', lambda raw: raw + b' '),
                 (short.BASE + '/source/analysis/campaign7/b1_mayan.py', lambda raw: raw + b' '),
                 ('text/lp2-00.txt', lambda raw: raw + b' '),
                 ('data/local-run-inputs.json', lambda raw: json.dumps({**json.loads(raw), 'pages': [{**p, 'raw': p['raw'] + 'x'} if p['id'] == 'lp2-00' else p for p in json.loads(raw)['pages']]}).encode()),
                 (short.BASE + '/record.json', lambda raw: json.dumps({**json.loads(raw), 'id': 'wrong-owner'}).encode())]
        for name, mutate in cases:
            target = short.ROOT / name
            def changed(path):
                raw = original_read(path)
                return mutate(raw) if path == target else raw
            with self.subTest(path=name), patch.object(Path, 'read_bytes', changed):
                with self.assertRaises(ValueError):
                    short.source()

    def test_actual_browser_source_validator_checks_all_54_synthetic_witnesses_only(self):
        payload = {'record': self.value, 'bundle': json.loads((short.ROOT / 'data/local-run-inputs.json').read_bytes())}
        code = r"""const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto'),E=require('./local-experiment.js'),A=require('./authored-finite-followup.js'),input=JSON.parse(fs.readFileSync(0,'utf8')),bytes=Buffer.from(JSON.stringify(input.record)),recipe=input.record.browser_followups.find(r=>r.id==='short-numeric-keys-reset-language'),hash=v=>crypto.createHash('sha256').update(v).digest('hex'),origin={recordId:input.record.id,followupId:recipe.id,recordSha256:hash(bytes),protocolSha256:hash(E.stable(recipe))},run=E.run;let controls=0;E.run=task=>{assert.deepEqual(task.pages.map(p=>p.id),['lp1-01']);assert(task.title.toLowerCase().includes('synthetic'));assert.equal(task.criterion.values.length,184);controls++;return run(task);};A.fromSource(origin,{sourceBytes:bytes,bundle:input.bundle,crypto:crypto.webcrypto}).then(plan=>{assert.equal(controls,54);assert.equal(plan.domain.totalCases,2970);console.log(JSON.stringify({controls,cases:plan.domain.totalCases}));}).catch(error=>{console.error(error);process.exitCode=1;});"""
        completed = subprocess.run(['node', '-e', code], input=json.dumps(payload, ensure_ascii=True),
                                   cwd=short.ROOT, text=True, encoding='utf-8', capture_output=True, check=True)
        self.assertEqual(json.loads(completed.stdout), {'controls': 54, 'cases': 2970})

    def test_synthetic_settings_output_hash_and_input_pins_cannot_be_changed(self):
        authored.validate_recipe(self.recipe, short.ROOT, set(short.PAGES))
        for mutation in ('settings', 'digest', 'input'):
            altered = copy.deepcopy(self.recipe)
            if mutation == 'settings':
                altered['control']['members'][0]['settings'] = []
            elif mutation == 'digest':
                altered['control']['members'][0]['control']['expected_result_sha256'] = '0' * 64
            else:
                altered['inputs']['pages'][0]['text_sha256'] = '0' * 64
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                authored.validate_recipe(altered, short.ROOT, set(short.PAGES))


if __name__ == '__main__':
    unittest.main()
