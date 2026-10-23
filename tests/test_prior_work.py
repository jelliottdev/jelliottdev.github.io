"""An unknown or ambiguous source must not masquerade as an empty prior-work search."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research'))
import prior_work


class SourceLookupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'research').mkdir()
        (self.root / 'experiments/records').mkdir(parents=True)
        self.entries = [
            {'source_id': 'R24-C2-SKIP-BY-TWO', 'candidate_records': [],
             'source_evidence_urls': ['https://example.invalid/pinned/first.py']},
            {'source_id': 'R24-C2-EXT-SKIP-GENERATORS', 'candidate_records': [],
             'source_evidence_urls': ['https://example.invalid/pinned/second.py']},
        ]
        self.write('public-attempt-inventory.json', {'entries': self.entries})
        self.write('fixture-input-dependency-2026-10-23.json', {
            'schema': 'internal-source-input-dependency-v1', 'checked_on': '2026-10-23',
            'revision': 'pinned', 'effect': 'Exact panel unavailable; no plaintext conclusion.',
            'confirmed_dependent_source_ids': [
                {'source_id': self.entries[1]['source_id'], 'source_path': 'pinned/second.py'}],
            'missing_inputs': [{'path': 'models/panel.npz', 'status': 'not present at checked revision'}],
        })
        self.patcher = patch.object(prior_work, 'ROOT', self.root)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def write(self, filename, data):
        (self.root / 'research' / filename).write_text(json.dumps(data), encoding='utf-8')

    def test_case_insensitive_exact(self):
        result = prior_work.lookup(source_id='r24-c2-skip-by-two')
        self.assertEqual(result['source_lookup'], 'exact')
        self.assertEqual(result['source_entry']['source_id'], self.entries[0]['source_id'])
        self.assertEqual(result['input_dependencies'], [])

    def test_unique_shorthand_exposes_recorded_input_check(self):
        result = prior_work.lookup(source_id='r24-c2-ext')
        self.assertEqual(result['source_lookup'], 'unique-prefix')
        self.assertEqual(result['source_entry']['source_id'], self.entries[1]['source_id'])
        note = result['input_dependencies'][0]
        self.assertEqual(note['revision'], 'pinned')
        self.assertEqual(note['missing_inputs'][0]['path'], 'models/panel.npz')
        self.assertIn('not a fresh probe', note['usage'])

    def test_ambiguous_prefix_never_selects_one(self):
        result = prior_work.lookup(source_id='R24-C2')
        self.assertEqual(result['source_lookup'], 'ambiguous')
        self.assertIsNone(result['source_entry'])
        self.assertEqual(len(result['source_candidates']), 2)

    def test_unknown_id_is_explicit_even_when_path_matches(self):
        result = prior_work.lookup(source_id='missing', source_path='pinned/second.py')
        self.assertEqual(result['source_lookup'], 'not-found')
        self.assertIsNone(result['source_entry'])

    def test_exact_source_path_can_find_its_ledger_entry(self):
        result = prior_work.lookup(source_path='pinned/second.py')
        self.assertEqual(result['source_lookup'], 'source-path')
        self.assertEqual(result['source_entry']['source_id'], self.entries[1]['source_id'])

    def test_repo_path_resolves_relative_ledger_evidence(self):
        result = prior_work.lookup(source_path='liber-primus/pinned/second.py')
        self.assertEqual(result['source_lookup'], 'source-path')
        self.assertEqual(result['source_entry']['source_id'], self.entries[1]['source_id'])
        self.assertEqual(len(result['input_dependencies']), 1)


if __name__ == '__main__':
    unittest.main()
