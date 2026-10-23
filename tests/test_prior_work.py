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

    def gate(self, source_id, path):
        self.write('fixture-execution-gate-2026-10-23.json', {
            'schema': 'internal-source-execution-gate-v1',
            'checked_on': '2026-10-23', 'revision': 'pinned',
            'source_id': source_id, 'source_paths': [path],
            'disposition': 'Known source gate cannot pass; no cipher exclusion.',
        })

    def test_source_gate_follows_unambiguous_ledger_shorthand(self):
        self.gate(self.entries[1]['source_id'], 'pinned/second.py')
        result = prior_work.lookup(source_id='r24-c2-ext')
        self.assertEqual(len(result['execution_gates']), 1)
        self.assertIn('not a fresh probe', result['execution_gates'][0]['usage'])

    def test_source_path_gate_does_not_require_a_ledger_entry(self):
        self.gate('other-repository-source', 'tools/source.py')
        result = prior_work.lookup(source_path='tools/source.py')
        self.assertEqual(result['source_lookup'], 'not-found')
        self.assertIsNone(result['source_entry'])
        self.assertEqual(len(result['execution_gates']), 1)

    def test_irrelevant_source_gate_is_not_applied(self):
        self.gate(self.entries[1]['source_id'], 'pinned/second.py')
        self.assertEqual(prior_work.lookup(source_id=self.entries[0]['source_id'])['execution_gates'], [])

    def test_gate_can_be_found_through_pinned_control_evidence(self):
        self.write('fixture-execution-gate-2026-10-23.json', {
            'schema': 'internal-source-execution-gate-v1',
            'source_id': 'recorded-source',
            'control_evidence': [{'path': 'pinned/control.py', 'sha256': 'receipt'}],
            'disposition': 'Saved positive control failed.',
        })
        result = prior_work.lookup(source_path='liber-primus/pinned/control.py')
        self.assertEqual(len(result['execution_gates']), 1)

    def test_recorded_audit_is_visible_without_claiming_replay(self):
        self.write('source-audit-register.json', {
            'schema': 'internal-source-audit-register-v1',
            'entries': [{'source_id': self.entries[1]['source_id'],
                         'independently_replayed_by_audit': False,
                         'next_action': 'Check source control before target run.'}],
        })
        result = prior_work.lookup(source_id='r24-c2-ext')
        self.assertEqual(len(result['source_audits']), 1)
        self.assertFalse(result['source_audits'][0]['independently_replayed_by_audit'])
        self.assertEqual(prior_work.lookup(source_id='missing')['source_audits'], [])

    def test_shared_control_is_reusable_only_for_matching_source(self):
        self.write('shared-control-register.json', {
            'schema': 'internal-shared-control-register-v1', 'entries': [{
                'source_ids': [self.entries[1]['source_id']],
                'source_paths': ['pinned/control.py'],
                'scope': 'Exact planted-message recovery, not a manuscript result.',
            }],
        })
        self.assertEqual(len(prior_work.lookup(source_id='r24-c2-ext')['shared_controls']), 1)
        self.assertEqual(len(prior_work.lookup(source_path='liber-primus/pinned/control.py')['shared_controls']), 1)
        self.assertEqual(prior_work.lookup(source_id=self.entries[0]['source_id'])['shared_controls'], [])


if __name__ == '__main__':
    unittest.main()
