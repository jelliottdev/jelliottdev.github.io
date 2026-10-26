"""Discovery stays presentation-only; selected exports retain complete evidence."""
import copy
import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import build_experiments as builder

ROOT = Path(__file__).resolve().parents[1]


class DiscoveryProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_registry = (ROOT / 'data/experiments.json').read_bytes()
        cls.records = json.loads(cls.raw_registry)['records']
        cls.original = json.loads((ROOT / 'data/experiment-index.json').read_bytes())['records']
        cls.before = copy.deepcopy(cls.records)
        cls.projected = [builder.discovery_record(ROOT, record) for record in cls.records]

    def test_published_target_manifest_is_tiny_and_contains_only_current_published_ids(self):
        value = builder.published_record_ids(self.records)
        self.assertEqual(value, {'schema': 'liberpedia-published-record-ids-v1',
                                 'ids': [record['id'] for record in self.records]})
        self.assertLess(len(json.dumps(value, separators=(',', ':')).encode()), 16000)
        for records in ([self.records[0], self.records[0]],
                        [{**self.records[0], 'status': 'draft'}],
                        [{**self.records[0], 'id': 'idea-' + 'a' * 64}],
                        [{**self.records[0], 'id': '../escape'}]):
            with self.assertRaises(ValueError):
                builder.published_record_ids(records)
        self.assertEqual(self.records, self.before)

    def test_temp_build_emits_the_ids_manifest_without_bodies_or_draft_ids(self):
        from test_experiments import RegistryTests
        fixture = RegistryTests()
        fixture.setUp()
        try:
            fixture.run_build()
            path = fixture.root / 'data/research-record-ids.json'
            self.assertEqual(path.read_bytes(), b'{"schema":"liberpedia-published-record-ids-v1","ids":["test-record"]}\n')
            fixture.run_build({**fixture.record, 'status': 'draft'})
            self.assertEqual(json.loads(path.read_bytes())['ids'], [])
        finally:
            fixture.tearDown()

    def test_all_published_members_labels_and_existing_fields_are_preserved(self):
        self.assertGreater(len(self.records), 0)
        self.assertEqual([r['id'] for r in self.projected], [r['id'] for r in self.original])
        for current, prior, source in zip(self.projected, self.original, self.records):
            for key, value in prior.items():
                self.assertEqual(current[key], value, source['id'] + '.' + key)
            self.assertEqual(current.get('reader_title', current['title']), source.get('reader_title', source['title']))
            self.assertEqual(current['source_finding'], source['finding'])
            self.assertEqual(current['status'], 'published')
            for key in ('next_steps', 'reader_finding', 'reader_limit', 'reader_test', 'reader_question',
                        'reader_title', 'reader_intro', 'research_questions', 'variant', 'materials',
                        'discovery', 'recorded_comparison'):
                self.assertEqual(key in current, key in source)
                if key in source:
                    self.assertEqual(current[key], source[key])
        self.assertEqual(self.records, self.before)

    def test_exact_export_and_canonical_source_hashes_are_distinct_lazy_references(self):
        for current, source in zip(self.projected, self.records):
            identifier = source['id']
            exported = builder.record_export_bytes(source)
            raw = (ROOT / f'experiments/records/{identifier}/record.json').read_bytes()
            self.assertEqual(current['record_source'], {'path': f'reference/experiments/{identifier}.json',
                                                       'sha256': hashlib.sha256(exported).hexdigest()})
            self.assertEqual(current['authored_source'], {'path': f'experiments/records/{identifier}/record.json',
                                                         'sha256': hashlib.sha256(raw).hexdigest()})
            self.assertEqual(json.loads(exported), source)
            self.assertEqual(exported, (ROOT / current['record_source']['path']).read_bytes())
            self.assertNotIn('article', current)
            self.assertNotIn('reproduction', current)
            self.assertNotIn('browser_followups', current)

    def test_followups_are_bounded_discovery_descriptors_not_executable_recipes(self):
        count = 0
        for current, source in zip(self.projected, self.records):
            envelope = current['followup_discovery']
            self.assertEqual(set(envelope), {'schema', 'items'})
            self.assertEqual(envelope['schema'], 'liberpedia-followup-discovery-v1')
            self.assertEqual(len(envelope['items']), len(source.get('browser_followups', [])))
            completed = {q.get('followup') for q in source.get('research_questions', []) if q['state'] == 'tested'}
            for item, recipe in zip(envelope['items'], source.get('browser_followups', [])):
                count += 1
                expected = {'id', 'title', 'question', 'scope_change', 'limitation', 'kind', 'evaluation_kind',
                            'available', 'protocol_sha256'} | ({'motivation'} if 'motivation' in recipe else set())
                self.assertEqual(set(item), expected)
                for key in ('id', 'title', 'question', 'scope_change', 'limitation', 'motivation'):
                    if key in recipe:
                        self.assertEqual(item[key], recipe[key])
                self.assertEqual(item['kind'], recipe.get('kind', 'fixed'))
                criterion = recipe['card']['rules']['evaluation']['value']
                self.assertEqual(item['evaluation_kind'], criterion['kind'] if isinstance(criterion, dict) else criterion)
                self.assertEqual(item['available'], recipe['id'] not in completed)
                protocol = json.dumps(recipe, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
                self.assertEqual(item['protocol_sha256'], hashlib.sha256(protocol).hexdigest())
                for forbidden in ('card', 'inputs', 'control', 'task', 'members', 'alphabet', 'steps'):
                    self.assertNotIn(forbidden, item)
        self.assertEqual(count, 23)

    def test_projection_size_remains_below_half_of_omnibus_even_with_all_recipe_hints(self):
        raw = (json.dumps({'schema': 'liberpedia-experiment-discovery-v1', 'records': self.projected},
                          ensure_ascii=False, indent=2) + '\n').encode()
        hints = json.dumps([r['followup_discovery'] for r in self.projected], ensure_ascii=False,
                           separators=(',', ':')).encode()
        self.assertLess(len(raw), len(self.raw_registry) * .5)
        self.assertLess(len(gzip.compress(raw)), len(gzip.compress(self.raw_registry)) * .5)
        self.assertLess(len(hints), 50000)
        self.assertEqual(self.records, self.before)

    def test_tested_is_an_authored_hint_and_cannot_mutate_or_replace_source_protocol(self):
        record = copy.deepcopy(next(r for r in self.records if r.get('browser_followups')))
        recipe = record['browser_followups'][0]
        record['research_questions'] = [{'id': 'synthetic-test', 'state': 'tested', 'followup': recipe['id']}]
        projected = builder.discovery_record(ROOT, record)
        self.assertFalse(projected['followup_discovery']['items'][0]['available'])
        # A newer result is not inferred from declaration presence or from the
        # descriptor title; exact source recipe identity must still agree.
        record['browser_followups'][0]['title'] = 'Not the canonical source recipe'
        with self.assertRaisesRegex(ValueError, 'differs from its exact source'):
            builder.discovery_record(ROOT, record)
        with self.assertRaisesRegex(ValueError, 'Invalid discovery record ID'):
            builder.discovery_record(ROOT, {**record, 'id': '../outside'})


if __name__ == '__main__':
    unittest.main()
