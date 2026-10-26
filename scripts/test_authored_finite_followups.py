"""Independent finite authored witnesses; synthetic execution only, no exports."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import authored_finite_followups as authored
import browser_followups as fixed
import finite_followup_cards as finite
from test_finite_followup_cards import card

ROOT = Path(__file__).resolve().parents[1]


def real_card():
    plan = json.loads((ROOT / 'experiments/records/lp2-known-vigenere-keys/plan.json').read_text(encoding='utf-8'))
    keys = [key['indices'][phase:] + key['indices'][:phase]
            for key in plan['keys'] for phase in range(len(key['indices']))]
    value = card([{'id': 'repeating_key', 'reset': 'page'}],
                 [{'operation': 0, 'name': 'key', 'values': keys},
                  {'operation': 0, 'name': 'direction', 'values': ['subtract', 'add']}], plan['pages'])
    value['rules']['evaluation'] = {'status': 'specified', 'value': copy.deepcopy(fixed.LANGUAGE_CRITERION)}
    return value


def fixture():
    value = authored.construct_followup(ROOT, card=real_card(), identifier='known-keys-language-fixture',
        title='Compare two explicit known-key families with language samples',
        question='How do these complete fixed outputs compare with the maintained references?',
        scope_change='Use the declared phases and directions without changing any target transformation.',
        limitation='A language comparison is not a recovered reading.',
        motivation='Compare the exact declared outputs with fixed language references.')
    # Keep the legacy admission fixture; compact admission has its own end-to-end coverage.
    value['control'] = authored.storage.expand(value['control'])
    return value


class AuthoredFinite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original = fixed.runner.run
        cls.executed = []
        def synthetic_only(task):
            if [p['id'] for p in task['pages']] != ['lp1-01'] or 'synthetic' not in task['title'].lower():
                raise AssertionError('No target task may execute')
            cls.executed.append(copy.deepcopy(task))
            return original(task)
        with patch.object(fixed.runner, 'run', side_effect=synthetic_only):
            cls.recipe = fixture()
        cls.warning, cls.expected = fixed.warning_plaintext(ROOT, fixed.alphabet(ROOT))

    def test_all_42_independent_complete_controls_and_shared_target_pins(self):
        value = copy.deepcopy(self.recipe); before = copy.deepcopy(value)
        expanded = finite.compile_card(value['card'])
        self.assertEqual(len(value['control']['members']), 42)
        self.assertEqual(expanded['declaration']['caseCount'], 2352)
        for member, variant in zip(value['control']['members'], expanded['variants']):
            control = member['control']; task = control['task']
            self.assertEqual(member['settings'], variant['settings'])
            self.assertEqual(task['steps'], variant['compiled']['steps'])
            self.assertEqual(task['criterion'], {'kind': 'exact-prefix', 'values': self.expected})
            self.assertEqual(len(self.expected), 184)
            result = fixed.runner.run(task)
            self.assertEqual(result['transformed'][0]['text'], self.warning)
            self.assertEqual(control['expected_result_sha256'], fixed.digest(result))
        authored.validate_followups([value], ROOT, set(value['card']['scope']['value']['pages']))
        self.assertEqual(value, before)
        self.assertTrue(all(len(task['criterion']['values']) == 184 for task in self.executed))
        self.assertEqual(len(value['inputs']['pages']), 56)

    def test_missing_duplicate_wrong_order_and_unknown_settings_rejected(self):
        mutations = [lambda m: m.pop(), lambda m: m.append(copy.deepcopy(m[0])),
                     lambda m: m.__setitem__(1, copy.deepcopy(m[0])),
                     lambda m: m.reverse(),
                     lambda m: m[0]['settings'][0].update(value='wrong'),
                     lambda m: m[0]['settings'].append(copy.deepcopy(m[0]['settings'][0])),
                     lambda m: m[0].update(extra=1)]
        for mutate in mutations:
            value = copy.deepcopy(self.recipe); mutate(value['control']['members'])
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): authored.validate_recipe(value, ROOT)

    def test_control_program_alphabet_hash_and_complete_output_are_bound(self):
        mutations = [lambda c: c.update(expected_result_sha256='0' * 64),
                     lambda c: c.update(label='Known manuscript control'),
                     lambda c: c['task']['steps'][0].update(direction='multiply'),
                     lambda c: c['task']['alphabet'][0].update(prime=999),
                     lambda c: c['task']['pages'][0].update(text='ᚠ'),
                     lambda c: c['task']['criterion'].update(kind='measurement'),
                     lambda c: c['task']['criterion']['values'].__setitem__(0, 0)]
        for mutate in mutations:
            value = copy.deepcopy(self.recipe); mutate(value['control']['members'][0]['control'])
            with self.subTest(mutate=mutate), self.assertRaises((ValueError, KeyError)):
                authored.validate_recipe(value, ROOT)
        value = copy.deepcopy(self.recipe)
        control = value['control']['members'][0]['control']; task = control['task']
        task['criterion']['values'] = task['criterion']['values'][:12]
        task['taskId'] = fixed.runner.task_identity(task)
        control['expected_result_sha256'] = fixed.digest(fixed.runner.run(task))
        with self.assertRaisesRegex(ValueError, 'every synthetic output rune'): authored.validate_recipe(value, ROOT)
        value = copy.deepcopy(self.recipe)
        task = value['control']['members'][0]['control']['task']
        task['pages'].append({**task['pages'][0], 'id': 'lp1-03'})
        task['taskId'] = fixed.runner.task_identity(task)
        with self.assertRaisesRegex(ValueError, 'exactly one synthetic page'): authored.validate_recipe(value, ROOT)
        value = copy.deepcopy(self.recipe)
        task = value['control']['members'][0]['control']['task']
        task['pages'][0]['text'] = 'ᚠ' * 257
        task['taskId'] = fixed.runner.task_identity(task)
        with self.assertRaisesRegex(ValueError, 'every synthetic output rune'): authored.validate_recipe(value, ROOT)

    def test_source_card_and_shared_input_pins_cannot_mutate(self):
        mutations = [lambda r: r['inputs'].update(alphabet_sha256='0' * 64),
                     lambda r: r['inputs'].update(version='reviewed'),
                     lambda r: r['inputs']['pages'][0].update(text_sha256='0' * 64),
                     lambda r: r['inputs']['pages'].reverse(),
                     lambda r: r['inputs']['pages'].pop(),
                     lambda r: r['card']['rules']['evaluation']['value'].update(modelSha256='0' * 64),
                     lambda r: r['card']['rules']['evaluation']['value'].update(threshold=0.7),
                     lambda r: r['card']['method']['value']['operations'][0].update(reset='word')]
        for mutate in mutations:
            value = copy.deepcopy(self.recipe); mutate(value)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): authored.validate_recipe(value, ROOT)
        with self.assertRaisesRegex(ValueError, 'page order/id'): authored.validate_recipe(self.recipe, ROOT, {'lp2-00'})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'data/pages').mkdir(parents=True)
            (root / 'data/index.json').write_bytes((ROOT / 'data/index.json').read_bytes())
            source = json.loads((ROOT / 'data/pages/lp2-00.json').read_text(encoding='utf-8'))
            source['raw'] += 'ᚠ'
            (root / 'data/pages/lp2-00.json').write_text(json.dumps(source), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'text pin mismatch'): authored.validate_recipe(self.recipe, root)

    def test_generic_composed_primitive_controls_and_unencodable_member_rejection(self):
        source = card([{'id': 'affine', 'b': 7}, {'id': 'repeating_key', 'key': [1, 2]}],
                      [{'operation': 0, 'name': 'a', 'values': [2, 1]},
                       {'operation': 1, 'name': 'reset', 'values': ['line', 'word']},
                       {'operation': 1, 'name': 'direction', 'values': ['add', 'subtract']}])
        result = authored.construct_followup(ROOT, card=source, identifier='generic-composed', title='Composed control',
            question='Does the declared composition implement its exact output?', scope_change='Fixed synthetic fixture.',
            limitation='Implementation check only.')
        self.assertEqual(len(result['control']['members']), 8)
        source['rules']['searchBounds']['value']['parameters'][0]['values'] = [0, 1]
        with self.assertRaisesRegex(ValueError, 'noninvertible'): authored.construct_followup(ROOT, card=source,
            identifier='noninvertible', title='Unencodable member', question='Explicit invalid inverse?',
            scope_change='Fixture only.', limitation='Must reject rather than drop a member.')

    def test_fixed_branch_unchanged_and_global_metadata_id_rules(self):
        path = ROOT / 'experiments/records/lp2-known-vigenere-keys/record.json'
        source = json.loads(path.read_text(encoding='utf-8'))['browser_followups']
        before = copy.deepcopy(source)
        self.assertIs(authored.validate_followups(source, ROOT), source)
        self.assertEqual(source, before)
        mixed = [copy.deepcopy(source[0]), copy.deepcopy(self.recipe)]
        self.assertIs(authored.validate_followups(mixed, ROOT), mixed)
        mixed[1]['id'] = mixed[0]['id']
        with self.assertRaisesRegex(ValueError, 'duplicate'): authored.validate_followups(mixed, ROOT)
        for mutate in [lambda r: r.update(kind='unknown'), lambda r: r.update(extra=1),
                       lambda r: r.update(motivation='<not plain>'),
                       lambda r: r['control'].update(kind='one-control-is-enough')]:
            value = copy.deepcopy(self.recipe); mutate(value)
            with self.assertRaises(ValueError): authored.validate_recipe(value, ROOT)

    def test_no_source_results_or_exports_written(self):
        paths = [ROOT / 'experiments/records/lp2-known-vigenere-keys/results.json',
                 ROOT / 'experiments/records/lp2-known-vigenere-keys/record.json',
                 ROOT / 'reference/experiments/lp2-known-vigenere-keys.json']
        before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        authored.validate_recipe(self.recipe, ROOT)
        self.assertEqual(before, {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})

    def test_builder_limits_entire_finite_parent_source_before_recipe_validation(self):
        import build_experiments as builder
        raw = {'id': 'test-record', 'status': 'draft', 'title': 'Fixture', 'question': 'Question?',
               'summary': 'Summary.', 'finding': 'Finding.', 'limitations': 'Limits.',
               'next_steps': 'Next.', 'outcome': 'inconclusive', 'scope': {'pages': ['lp2-15']},
               'browser_followups': [copy.deepcopy(self.recipe)], 'padding': 'x' * (2 * 1024 * 1024)}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); path = root / 'experiments/records/test-record/record.json'
            path.parent.mkdir(parents=True); path.write_text(json.dumps(raw), encoding='utf-8')
            with patch.object(builder, 'validate_followups') as dispatch:
                with self.assertRaisesRegex(ValueError, 'source record exceeds 2 MiB'):
                    builder.validate_record(root, path, {'lp2-15'})
                dispatch.assert_not_called()
            raw.pop('padding'); path.write_text(json.dumps(raw), encoding='utf-8')
            with patch.object(builder, 'validate_followups', side_effect=ValueError('dispatcher reached')) as dispatch:
                with self.assertRaisesRegex(ValueError, 'dispatcher reached'):
                    builder.validate_record(root, path, {'lp2-15'})
                dispatch.assert_called_once()
            self.assertFalse((root / 'data').exists())
            self.assertFalse((root / 'reference').exists())

    def test_finite_question_reference_preserves_exact_scope_and_editorial_state(self):
        from research_questions import protocol_reference, validate_research_questions
        question = {'id': 'language-comparison', 'question': 'How do the fixed outputs compare?',
                    'state': 'open', 'note': 'Language similarity does not establish a reading.',
                    'records': [], 'followup': self.recipe['id'],
                    'protocol': {'id': 'finite-settings-output', 'version': 1}}
        record = {'id': 'fixture-record', 'browser_followups': [copy.deepcopy(self.recipe)],
                  'research_questions': [question]}
        before = copy.deepcopy(record)
        validate_research_questions([question], record)
        reference = protocol_reference(question, record)
        self.assertEqual(reference, {'id': 'finite-settings-output', 'version': 1,
                                    'followupId': self.recipe['id'], 'inputs': self.recipe['inputs']})
        self.assertEqual(record, before)
        reference['inputs']['pages'].pop(); self.assertEqual(record, before)
        for mutate in [lambda r: r['browser_followups'][0].pop('kind'),
                       lambda r: r['browser_followups'][0]['inputs']['pages'].reverse(),
                       lambda r: r['browser_followups'][0]['inputs']['pages'].pop(),
                       lambda r: r['browser_followups'][0]['inputs'].update(version='reviewed'),
                       lambda r: r['browser_followups'][0]['inputs'].update(alphabet_sha256='invalid'),
                       lambda r: r['browser_followups'][0]['card']['rules']['searchBounds']['value']['parameters'][0].update(name='unknown'),
                       lambda r: r['research_questions'][0]['protocol'].update(id='fixed-program-prefix'),
                       lambda r: r['research_questions'][0]['protocol'].update(version=True),
                       lambda r: r['research_questions'][0].update(state='tested')]:
            changed = copy.deepcopy(record); mutate(changed)
            with self.subTest(mutate=mutate), self.assertRaisesRegex(ValueError, 'research_questions'):
                validate_research_questions(changed['research_questions'], changed)
        changed = copy.deepcopy(record); changed['research_questions'][0].update(state='tested', records=['another-record'])
        validate_research_questions(changed['research_questions'], changed)
        self.assertEqual(changed['research_questions'][0]['state'], 'tested')


if __name__ == '__main__':
    unittest.main()
