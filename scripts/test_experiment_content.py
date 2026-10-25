"""Single-source authoring must update every public view without duplicate prose."""
import copy
import hashlib
import json
import unittest
import zipfile
from pathlib import Path
import test_experiments as fixtures
from build_experiments import build, validate_record, checker_payload
from build_experiment_bundles import build as bundle
from preflight_experiments import preflight
from experiment_content import SCHEMA, compile_content


class ContentTests(unittest.TestCase):
    setUp = fixtures.RegistryTests.setUp
    tearDown = fixtures.RegistryTests.tearDown

    def source(self):
        d = copy.deepcopy(self.record)
        d['schema'] = SCHEMA
        d['classification'] = {'kind': 'measurement', 'methods': ['feedback'], 'map_parent': 'method:feedback'}
        d['result'] = {'finding': d.pop('finding'), 'limits': d.pop('limitations'), 'next_steps': d.pop('next_steps')}
        d.pop('summary')
        d['analysis'] = '# Exact technical account\n\n' + 'The tested procedure and controls are documented here. ' * 8 + '\n'
        return d

    def write(self, raw):
        p = self.root / 'experiments/records/test-record/record.json'
        p.write_text(json.dumps(raw), encoding='utf-8')
        return p

    def files(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_preflight_without_derived_article_is_read_only(self):
        raw = self.source()
        p = self.write(raw)
        (p.parent / 'article.md').unlink()
        (self.root / 'data/experiments.json').write_text('{"records":[]}')
        before = self.files()
        checked = preflight(['test-record'], self.root)[0]
        self.assertEqual(checked['article'], raw['analysis'])
        self.assertEqual(before, self.files())

    def test_single_edit_reaches_indexes_account_and_archive(self):
        raw = self.source(); self.write(raw)
        records = build(self.root)
        (self.root / 'scripts').mkdir()
        (self.root / 'scripts/verify_bundle.py').write_text('# Fixture verifier')
        bundle(self.root, records[0])
        raw['result']['finding'] = 'The next checked result, authored once.'
        raw['analysis'] += '\nA new technical explanation.\n'
        self.write(raw)
        records = build(self.root); bundle(self.root, records[0])
        r = records[0]
        for key in ('finding', 'reader_finding', 'summary'):
            self.assertEqual(r[key], raw['result']['finding'])
        for file in ('data/experiment-index.json', 'data/checker-records.json', 'reference/experiments/test-record.json'):
            exported = json.loads((self.root / file).read_bytes())
            row = exported['records'][0] if 'records' in exported else exported
            self.assertEqual(row['finding'], raw['result']['finding'])
        self.assertNotIn('analysis', r)
        self.assertNotIn('result', r)
        self.assertEqual((self.root / r['article_path']).read_bytes(), raw['analysis'].encode())
        with zipfile.ZipFile(self.root / 'downloads/experiments/test-record.zip') as z:
            self.assertEqual(z.read(r['article_path']), raw['analysis'].encode())
            self.assertEqual(json.loads(z.read('experiments/records/test-record/record.json')), raw)
            self.assertIn(raw['result']['finding'], z.read('START-HERE-test-record.txt').decode())
        before = self.files(); build(self.root); bundle(self.root, records[0])
        self.assertEqual(before, self.files())

    def test_finding_sections_are_selected_from_one_authored_account(self):
        raw = self.source()
        raw['analysis'] = '## Visible evidence\n\n| Rule | First mismatch |\n| --- | --- |\n| Fixed rule | Rune 2 |\n\n## Detailed method\n\n' + 'Technical details remain here. ' * 10
        raw['presentation'] = {'finding_sections': ['Visible evidence']}
        self.write(raw)
        record = build(self.root)[0]
        self.assertEqual(record['reader_sections'], ['Visible evidence'])
        self.assertEqual(record['article'], raw['analysis'])
        self.assertNotIn('presentation', record)
        for sections in [['Missing heading'], ['Visible evidence', 'Visible evidence'], [' Visible evidence'], ['x' * 121], [None]]:
            raw['presentation']['finding_sections'] = sections
            self.write(raw)
            before = self.files()
            with self.subTest(sections=sections), self.assertRaises(ValueError):
                build(self.root)
            self.assertEqual(before, self.files())
        raw['presentation'] = {'unregistered': []}
        with self.assertRaises(ValueError):
            compile_content(raw)

    def test_duplicate_and_invalid_sources_fail_before_writes(self):
        for key in ('finding', 'reader_finding', 'reader_limit', 'summary', 'article'):
            raw = self.source(); raw[key] = 'Conflicting second version'; self.write(raw)
            before = self.files()
            with self.assertRaisesRegex(ValueError, 'derives these fields'):
                build(self.root)
            self.assertEqual(before, self.files())
        for mutate in (lambda d: d['result'].update(extra='bad'), lambda d: d['result'].update(finding='x'*701), lambda d: d.update(schema='unknown')):
            raw = self.source(); mutate(raw)
            with self.assertRaises(ValueError):
                compile_content(raw)

    def test_analysis_hash_uses_source_bytes_including_line_endings(self):
        raw = self.source(); raw['analysis'] = raw['analysis'].replace('\n', '\r\n')
        article = 'experiments/records/test-record/article.md'
        raw['reproduction']['inputs'].append({'path': article, 'sha256': hashlib.sha256(raw['analysis'].encode()).hexdigest()})
        p = self.write(raw)
        (p.parent / 'article.md').write_text('Stale generated file')
        r = validate_record(self.root, p, {'lp2-15'})
        self.assertEqual(r['article'], raw['analysis'])
        raw['analysis'] += 'Changed evidence'; self.write(raw)
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            validate_record(self.root, p, {'lp2-15'})

    def test_one_new_source_also_registers_existing_categories(self):
        raw = self.source(); self.write(raw)
        taxonomy = {'record_kinds': {'measurement': {'label': 'Measurement', 'description': 'A bounded comparison'}},
                    'record_kind_by_id': {}, 'families': [{'id': 'feedback', 'title': 'Feedback', 'aliases': [], 'related': []}]}
        (self.root / 'data/method-families.json').write_text(json.dumps(taxonomy))
        mapped = {'views': {'solving': {'nodes': [{'id': 'method:feedback', 'kind': 'method'}]}}}
        (self.root / 'data/research-map.json').write_text(json.dumps(mapped))
        records = build(self.root)
        registered = json.loads((self.root / 'data/method-families.json').read_bytes())
        self.assertEqual(registered['record_kind_by_id'], {'test-record': 'measurement'})
        self.assertEqual(registered['families'][0]['related'], ['test-record'])
        self.assertEqual(records[0]['method_topics'][0]['id'], 'feedback')
        raw['classification']['map_parent'] = 'invented:branch'; self.write(raw)
        before = self.files()
        with self.assertRaisesRegex(ValueError, 'existing branch'):
            build(self.root)
        self.assertEqual(before, self.files())

    def test_status_alone_withdraws_and_republishes_a_v2_record(self):
        raw = self.source(); self.write(raw)
        taxonomy = {'record_kinds': {'measurement': {'label': 'Measurement', 'description': 'A comparison'}},
                    'record_kind_by_id': {}, 'families': [{'id': 'feedback', 'title': 'Feedback', 'aliases': [], 'related': []}]}
        kind_path = self.root / 'data/method-families.json'
        kind_path.write_text(json.dumps(taxonomy))
        published = build(self.root)[0]
        account = (self.root / published['article_path']).read_bytes()
        raw['status'] = 'draft'; self.write(raw)
        self.assertEqual(build(self.root), [])
        retired = json.loads(kind_path.read_bytes())
        self.assertEqual(retired['record_kind_by_id'], {})
        self.assertEqual(retired['families'][0]['related'], [])
        self.assertFalse((self.root / 'reference/experiments/test-record.json').exists())
        self.assertEqual((self.root / published['article_path']).read_bytes(), account)
        # Preflight evaluates the selected draft as a proposed publication.
        self.assertEqual(preflight(['test-record'], self.root)[0]['status'], 'draft')
        raw['status'] = 'published'; self.write(raw)
        self.assertEqual(build(self.root)[0], published)

    def test_legacy_projection_is_unchanged(self):
        self.assertEqual(compile_content(self.record), self.record)
        self.assertIsNot(compile_content(self.record), self.record)


if __name__ == '__main__':
    unittest.main()
