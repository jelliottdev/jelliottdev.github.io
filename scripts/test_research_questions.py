"""Question linkage stays explicit, source-authored, and publication-atomic."""
import copy
import json
import shutil
import unittest

import test_experiments as fixtures
from build_experiments import build, validate_record
from experiment_content import SCHEMA
from research_questions import validate_research_questions, validate_research_question_refs, protocol_reference
from pathlib import Path
from preflight_experiments import preflight


def question(**changes):
    return {'id': 'section-control', 'question': 'Does the pattern survive section controls?',
            'state': 'open', 'note': 'The unrestricted comparison does not answer this question.',
            'records': [], **changes}


class QuestionShapeTests(unittest.TestCase):
    def test_selected_lag_five_question_binds_existing_recipe_without_recasting_the_search(self):
        root = Path(__file__).resolve().parents[1]
        record = json.loads((root / 'experiments/records/word-internal-affine-all-lags/record.json').read_text(encoding='utf-8'))
        before = copy.deepcopy(record)
        validate_research_questions(record['research_questions'], record)
        question = record['research_questions'][0]
        recipe = record['browser_followups'][0]
        reference = protocol_reference(question, record)
        self.assertEqual(reference['id'], 'word-boundary-sensitivity')
        self.assertEqual(reference['parameters'], {'lag': 5, 'a': 1, 'b': 0})
        self.assertEqual(reference['followupId'], 'lag-five-equality-non-rune-boundaries')
        self.assertEqual(reference['inputs'], recipe['inputs'])
        self.assertEqual(len(reference['inputs']['pages']), 56)
        self.assertEqual(question['state'], 'open')
        self.assertEqual(question['records'], [])
        self.assertIn('already selected', question['note'])
        self.assertIn('does not repeat the original 10,092-relation selection', question['note'])
        self.assertIn('not an independent discovery or a new significance test', recipe['limitation'])
        self.assertEqual(record, before)
        bad = copy.deepcopy(record)
        bad['research_questions'][0]['followup'] = 'lag-six-non-rune-boundaries'
        with self.assertRaisesRegex(ValueError, 'research_questions'):
            validate_research_questions(bad['research_questions'], bad)

    def test_fixed_prefix_reference_reuses_existing_compiler_and_exact_recipe_pins(self):
        root = Path(__file__).resolve().parents[1]
        record = json.loads((root / 'experiments/records/lp2-row-column-routes/record.json').read_text(encoding='utf-8'))
        before = copy.deepcopy(record)
        validate_research_questions(record['research_questions'], record)
        source = record['research_questions'][0]
        self.assertEqual(source['state'], 'tested')
        self.assertEqual(protocol_reference(source, record),
                         {'id': 'fixed-program-prefix', 'version': 1, 'followupId': source['followup'],
                          'inputs': record['browser_followups'][0]['inputs']})
        self.assertEqual(record, before)
        for mutate in (lambda r: r['research_questions'][0].pop('followup'),
                       lambda r: r['research_questions'][0]['protocol'].update(version=2),
                       lambda r: r['browser_followups'][0]['card']['method']['value']['operations'][0].update(id='unknown_operation'),
                       lambda r: r['browser_followups'][0]['card']['rules']['evaluation'].update(value={'kind': 'measurement'}),
                       lambda r: r['browser_followups'][0]['card']['rules']['evaluation']['value'].update(values=[29]),
                       lambda r: r['browser_followups'][0]['inputs']['pages'][0].update(text_sha256='bad'),
                       lambda r: r['browser_followups'][0]['card']['scope']['value']['pages'].pop()):
            bad = copy.deepcopy(record); mutate(bad)
            with self.assertRaisesRegex(ValueError, 'research_questions'):
                validate_research_questions(bad['research_questions'], bad)

    def test_maintained_protocols_resolve_owned_inputs_without_editorial_answers(self):
        root = Path(__file__).resolve().parents[1]
        for identifier in ('word-internal-affine-lags', 'wulfic-autokey-seed-families'):
            record = json.loads((root / 'experiments/records' / identifier / 'record.json').read_text(encoding='utf-8'))
            before = copy.deepcopy(record)
            validate_research_questions(record['research_questions'], record)
            source = record['research_questions'][0]
            resolved = protocol_reference(source, record)
            self.assertEqual(record, before)
            self.assertNotIn('state', resolved)
            if identifier == 'word-internal-affine-lags':
                recipe = record['browser_followups'][0]
                self.assertEqual(resolved['inputs'], recipe['inputs'])
                self.assertEqual(resolved['parameters'], {'lag': 6, 'a': 27, 'b': 24})
                source['state'], source['records'] = 'tested', ['another-published-record']
                self.assertEqual(protocol_reference(source, record), resolved)
                for mutate in (lambda r: r['research_questions'][0]['protocol'].update(id='unknown'),
                               lambda r: r['research_questions'][0]['protocol'].update(version=True),
                               lambda r: r['research_questions'][0]['protocol'].update(parameters={}),
                               lambda r: r['research_questions'][0].pop('followup'),
                               lambda r: r['browser_followups'][0]['card']['rules']['evaluation']['value'].update(a=26),
                               lambda r: r['browser_followups'][0]['card']['method']['value']['operations'].append({'id': 'reverse_runes'}),
                               lambda r: r['browser_followups'][0]['inputs']['pages'][0].update(text_sha256='bad'),
                               lambda r: r['browser_followups'][0]['card']['scope']['value']['pages'].pop(),
                               lambda r: r['browser_followups'][0]['card']['rules'].update(reset={'status': 'specified', 'value': 'word'})):
                    bad = copy.deepcopy(before); mutate(bad)
                    with self.assertRaisesRegex(ValueError, 'research_questions'):
                        validate_research_questions(bad['research_questions'], bad)
            else:
                self.assertEqual(resolved, {'id': 'deor-warning-opening', 'version': 1, 'familyId': 'deor-feedback-v1'})
                source['followup'] = 'another-rule'
                with self.assertRaises(ValueError):
                    protocol_reference(source, record)

    def check(self, questions, **changes):
        record = {'id': 'source-record', **changes}
        before = copy.deepcopy((questions, record))
        validate_research_questions(questions, record)
        self.assertEqual((questions, record), before)

    def test_optional_fields_are_not_added_and_recipe_is_explicit(self):
        self.check([question()])
        self.check([question(followup='section-shuffle')],
                   browser_followups=[{'id': 'section-shuffle'}])
        self.check([question(state='tested', records=['other-record'])])
        self.check([question(state='tested', records=['other-record'], followup='section-shuffle')], browser_followups=[{'id': 'section-shuffle'}])
        self.check([question(id='q' + 'a' * 99, question='x' * 300, note='y' * 700,
                             records=['record-' + str(n) for n in range(12)])])
        self.check([question(id='question-' + str(n)) for n in range(12)])

    def test_invalid_shape_and_limits(self):
        cases = [None, {}, [], [question()] * 13, [None],
                 [question(), question()], [question(extra='unsupported')],
                 [question(id='q' * 101)], [question(id='Not-a-slug')],
                 [question(state='complete')], [question(state='tested')],
                 [question(records='other-record')], [question(records=[False])],
                 [question(records=['source-record'])], [question(records=['same', 'same'])],
                 [question(records=['r' * 101])],
                 [question(records=['record-' + str(n) for n in range(13)])],
                 [question(followup='missing')], [question(followup=None)],
                 [question(state='tested', records=[], followup='section-shuffle')]]
        cases.append([question(followup='section-shuffle'), question(id='other-question', state='tested', records=['other-record'], followup='section-shuffle')])
        missing = question(); del missing['note']; cases.append([missing])
        for value in cases:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'research_questions'):
                self.check(value, browser_followups=[{'id': 'section-shuffle'}])

    def test_plain_prose_and_utf16_boundaries(self):
        for field, maximum in [('question', 300), ('note', 700)]:
            for value in ['', ' padded', 'trailing ', 'two\nlines', '<script>', '**bold**',
                          '[link](url)', '`code`', 'bad\x00value', 'paragraph\u2028break',
                          'unpaired\ud800surrogate',
                          'a' * (maximum + 1), '\U0001f332' * (maximum // 2 + 1)]:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.check([question(**{field: value})])


class QuestionBuildTests(unittest.TestCase):
    setUp = fixtures.RegistryTests.setUp
    tearDown = fixtures.RegistryTests.tearDown

    def write(self, record):
        path = self.root / 'experiments/records' / record['id'] / 'record.json'
        path.write_text(json.dumps(record), encoding='utf-8')
        return path

    def other(self, status='published'):
        shutil.copytree(self.root / 'experiments/records/test-record',
                        self.root / 'experiments/records/other-record')
        other = json.loads(json.dumps(self.record).replace('test-record', 'other-record'))
        other['status'] = status
        self.write(other)
        return other

    def files(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob('*') if path.is_file()}

    def test_no_field_remains_absent_in_all_exports(self):
        self.write(self.record)
        records = build(self.root)
        self.assertNotIn('research_questions', records[0])
        for name in ['data/experiments.json', 'data/checker-records.json',
                     'reference/experiments/test-record.json']:
            exported = json.loads((self.root / name).read_bytes())
            rows = exported['records'] if 'records' in exported else [exported]
            self.assertTrue(all('research_questions' not in row for row in rows))

    def test_v1_and_v2_export_exact_authored_links_without_defaults(self):
        self.other()
        for schema in [None, SCHEMA]:
            raw = copy.deepcopy(self.record)
            raw['research_questions'] = [question(state='tested', records=['other-record'])]
            if schema:
                raw['schema'] = schema
                raw['classification'] = {'kind': 'measurement', 'methods': ['feedback'],
                                         'map_parent': 'method:feedback'}
                raw['result'] = {'finding': raw.pop('finding'), 'limits': raw.pop('limitations'),
                                 'next_steps': raw.pop('next_steps')}
                raw.pop('summary')
                raw['analysis'] = '# Source account\n\n' + 'Documented controls and evidence. ' * 10
            self.write(raw)
            records = build(self.root)
            self.assertEqual(next(r for r in records if r['id'] == 'test-record')['research_questions'],
                             raw['research_questions'])
            for name in ['data/experiments.json', 'data/checker-records.json',
                         'reference/experiments/test-record.json']:
                exported = json.loads((self.root / name).read_bytes())
                row = next(r for r in exported['records'] if r['id'] == 'test-record') if 'records' in exported else exported
                self.assertEqual(row['research_questions'], raw['research_questions'])
                self.assertNotIn('followup', row['research_questions'][0])

    def test_validate_record_checks_local_shape_read_only(self):
        self.record['research_questions'] = [question(state='tested')]
        path = self.write(self.record)
        before = self.files()
        with self.assertRaisesRegex(ValueError, 'tested question needs a record link'):
            validate_record(self.root, path, {'lp2-15'})
        self.assertEqual(before, self.files())

    def test_unknown_draft_and_self_links_fail_before_any_output_changes(self):
        self.write(self.record); build(self.root)
        self.other(status='draft')
        # Existing generated outputs and stale account must survive a rejected build.
        (self.root / 'reference/experiments/obsolete.json').write_text('keep until validation passes')
        for reference in ['missing-record', 'other-record', 'test-record']:
            raw = copy.deepcopy(self.record)
            raw['schema'] = SCHEMA
            raw['classification'] = {'kind': 'measurement', 'methods': ['feedback'],
                                     'map_parent': 'method:feedback'}
            raw['result'] = {'finding': raw.pop('finding'), 'limits': raw.pop('limitations'),
                             'next_steps': raw.pop('next_steps')}
            raw.pop('summary'); raw['analysis'] = 'New unmaterialized account. ' * 12
            raw['research_questions'] = [question(state='tested', records=[reference])]
            self.write(raw)
            before = self.files()
            with self.subTest(reference=reference), self.assertRaisesRegex(ValueError, 'research_questions'):
                build(self.root)
            self.assertEqual(before, self.files())

    def test_cross_record_helper_does_not_infer_closure_or_modify_records(self):
        record = {'id': 'test-record', 'research_questions': [question(records=['other-record'])]}
        before = copy.deepcopy(record)
        validate_research_question_refs([record], {'test-record': record, 'other-record': {}})
        self.assertEqual(record, before)
        with self.assertRaisesRegex(ValueError, 'other published records'):
            validate_research_question_refs([record], {'test-record': record})

    def test_preflight_resolves_selected_batch_and_rejects_retired_evidence(self):
        self.write(self.record); build(self.root)
        other = self.other()
        self.record['research_questions'] = [question(state='tested', records=['other-record'])]
        self.write(self.record)
        before = self.files()
        # A new record is visible only when explicitly included in this proposed batch.
        with self.assertRaisesRegex(ValueError, 'other published records'):
            preflight(['test-record'], self.root)
        self.assertEqual(len(preflight(['test-record', 'other-record'], self.root)), 2)
        self.assertEqual(before, self.files())
        # A stale generated registry cannot keep a withdrawn v2 record as evidence.
        build(self.root)
        other['schema'] = SCHEMA
        other['status'] = 'draft'
        self.write(other)
        before = self.files()
        with self.assertRaisesRegex(ValueError, 'other published records'):
            preflight(['test-record'], self.root)
        self.assertEqual(before, self.files())


if __name__ == '__main__':
    unittest.main()
