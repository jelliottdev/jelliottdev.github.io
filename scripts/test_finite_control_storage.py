"""Storage-only sharing: fifteen real recipes, malformed forms and JS parity."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

import finite_control_storage as codec

ROOT = Path(__file__).resolve().parents[1]


def recipes():
    values = []
    for identifier in ('dukotah-fixed-numeric-keys', 'lp2-known-vigenere-keys', 'lp2-panel-prime-openings', 'lp2-prime-minus-one-openings', 'lp2-prime-openings', 'lp2-fibonacci-openings', 'lp2-totient-openings'):
        record = json.loads((ROOT / 'experiments/records' / identifier / 'record.json').read_bytes())
        values.extend(recipe for recipe in record['browser_followups'] if recipe.get('kind') == 'finite-settings')
    return values


def digest(value):
    return hashlib.sha256(codec.stable(value).encode()).hexdigest()


class FiniteControlStorage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_bytes = {
            ROOT / 'experiments/records' / identifier / 'record.json':
                (ROOT / 'experiments/records' / identifier / 'record.json').read_bytes()
            for identifier in ('dukotah-fixed-numeric-keys', 'lp2-known-vigenere-keys', 'lp2-panel-prime-openings', 'lp2-prime-minus-one-openings', 'lp2-prime-openings', 'lp2-fibonacci-openings', 'lp2-totient-openings')}
        cls.recipes = recipes()
        cls.legacy = codec.expand(cls.recipes[0]['control'])
        cls.shared = codec.compact(cls.legacy)

    def test_fifteen_actual_recipes_roundtrip_and_reduction(self):
        self.assertEqual(len(self.recipes), 15)
        for recipe in self.recipes:
            with self.subTest(recipe=recipe['id']):
                source_before = digest(recipe['control'])
                legacy = codec.expand(recipe['control'])
                before = digest(legacy)
                compact = codec.compact(legacy)
                self.assertEqual(compact['kind'], codec.COMPACT)
                self.assertEqual(digest(codec.expand(compact)), before)
                self.assertEqual(digest(legacy), before)
                ratio = len(codec.stable(compact).encode()) / len(codec.stable(legacy).encode())
                self.assertLessEqual(ratio, .65)
                self.assertEqual(compact, codec.compact(compact))
                self.assertEqual(digest(recipe['control']), source_before)
        for path, before in self.source_bytes.items():
            self.assertEqual(path.read_bytes(), before)

    def test_detached_values_and_expansion_sibling_independence(self):
        original = copy.deepcopy(self.legacy)
        compact = codec.compact(original)
        compact['alphabet'][0]['latin'] = 'Changed'
        compact['members'][0]['control']['task']['title'] = 'Changed'
        self.assertEqual(original, self.legacy)
        expanded = codec.expand(self.shared)
        expanded['members'][0]['control']['task']['alphabet'][0]['latin'] = 'Changed'
        expanded['members'][0]['control']['task']['criterion']['values'][0] = 28
        self.assertNotEqual(expanded['members'][0]['control']['task']['alphabet'],
                            expanded['members'][1]['control']['task']['alphabet'])
        self.assertEqual(self.shared, codec.compact(self.legacy))

    def test_nonshared_unsupported_and_unknown_legacy_are_lossless(self):
        values = [None, [], {'kind': 'another-legacy-format', 'metadata': [1.0, -0.0]},
                  {'kind': codec.LEGACY, 'members': []}]
        for field in ('alphabet', 'criterion'):
            value = copy.deepcopy(self.legacy)
            task = value['members'][1]['control']['task']
            if field == 'alphabet':
                task[field][0]['latin'] = 'Other'
            else:
                task[field]['values'][0] = (task[field]['values'][0] + 1) % 29
            values.append(value)
        unsupported = copy.deepcopy(self.legacy)
        for member in unsupported['members']:
            member['control']['task']['criterion'] = {'kind': 'measurement'}
        values.append(unsupported)
        extra = copy.deepcopy(self.legacy)
        extra['members'][0]['control']['task']['newField'] = 'retain me'
        values.append(extra)
        for value in values:
            self.assertEqual(codec.stable(codec.compact(value)), codec.stable(value))
            self.assertEqual(codec.stable(codec.expand(value)), codec.stable(value))

    def malformed(self):
        values = []
        def add(change):
            value = copy.deepcopy(self.shared)
            change(value)
            values.append(value)
        add(lambda v: v.update(kind='finite-program-controls-shared-v2'))
        add(lambda v: v.update(extra=1))
        add(lambda v: v.pop('alphabet'))
        add(lambda v: v.update(members=[]))
        add(lambda v: v.update(members=v['members'][:1] * 1025))
        add(lambda v: v.update(alphabet=v['alphabet'][:-1]))
        add(lambda v: v['alphabet'][0].update(extra=1))
        add(lambda v: v['alphabet'][0].update(prime=True))
        add(lambda v: v['criterion'].update(extra=1))
        add(lambda v: v['criterion'].update(values=[]))
        add(lambda v: v['criterion'].update(values=[True]))
        add(lambda v: v['criterion'].update(values=[29]))
        add(lambda v: v['criterion'].update(values=[0] * 257))
        add(lambda v: v['members'][0].update(extra=1))
        add(lambda v: v['members'][0]['control'].pop('expected_result_sha256'))
        add(lambda v: v['members'][0]['control'].update(expected_result_sha256='A' * 64))
        add(lambda v: v['members'][0]['control']['task'].update(alphabet=v['alphabet']))
        add(lambda v: v['members'][0]['control']['task'].update(criterion=v['criterion']))
        add(lambda v: v['members'][0]['control']['task'].pop('steps'))
        add(lambda v: v['members'][0]['control']['task'].update(taskId='invalid'))
        add(lambda v: v['members'][0]['control']['task']['pages'][0].update(extra=1))
        add(lambda v: v['members'][0]['settings'][0].update(extra=1))
        add(lambda v: v['members'][0].update(settings=v['members'][0]['settings'][:1] * 57))
        return values

    def test_recognized_compact_forms_fail_closed(self):
        for index, value in enumerate(self.malformed()):
            with self.subTest(case=index):
                for operation in (codec.compact, codec.expand):
                    with self.assertRaises(ValueError):
                        operation(value)

    def test_bounds_and_non_json_do_not_invoke_user_accessors(self):
        class Dangerous(dict):
            def items(self):
                raise AssertionError('Do not inspect custom object')
        class Getter:
            @property
            def kind(self):
                raise AssertionError('Do not invoke a getter')
        bad = [Dangerous(kind=codec.COMPACT), Getter(), (1, 2), {1: 'number key'},
               {'constructor': 1}, float('nan'), float('inf'), '\ud800', 'x' * (codec.LIMITS['bytes'] + 1)]
        deep = None
        for _ in range(codec.LIMITS['depth'] + 1):
            deep = [deep]
        bad.append(deep)
        for value in bad:
            with self.assertRaises(ValueError):
                codec.compact(value)
        with self.assertRaises(ValueError):
            codec.expand([None] * codec.LIMITS['nodes'])

    def test_expansion_bound_is_checked_after_sharing(self):
        value = copy.deepcopy(self.shared)
        value['criterion']['values'] = [0] * 256
        member = value['members'][0]
        value['members'] = [copy.deepcopy(member) for _ in range(1024)]
        # The compact representation fits but expansion must not amplify beyond
        # the same byte/node bound used by ordinary finite JSON admission.
        value = codec.compact(value)
        with self.assertRaises(ValueError):
            codec.expand(value)

    def test_javascript_cross_language_digest_and_rejection_parity(self):
        module = ROOT / 'finite-control-storage.js'
        self.assertTrue(module.exists(), 'Shared JavaScript codec must be available for parity')
        inputs = [codec.expand(recipe['control']) for recipe in self.recipes] + self.malformed()
        script = """
const fs=require('fs'),crypto=require('crypto'),C=require('./finite-control-storage.js');
const stable=v=>Array.isArray(v)?'['+v.map(stable).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}':JSON.stringify(v);
const digest=v=>crypto.createHash('sha256').update(stable(v)).digest('hex');
console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(v=>{try{const c=C.compact(v);return {ok:true,compact:digest(c),expanded:digest(C.expand(c))}}catch{return {ok:false}}})));
"""
        actual = json.loads(subprocess.check_output(['node', '-e', script], cwd=ROOT,
                                                    input=json.dumps(inputs, ensure_ascii=False), encoding='utf8'))
        for index, (value, result) in enumerate(zip(inputs, actual)):
            with self.subTest(case=index):
                try:
                    compact = codec.compact(value)
                    expected = {'ok': True, 'compact': digest(compact), 'expanded': digest(codec.expand(compact))}
                except ValueError:
                    expected = {'ok': False}
                self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
