"""Check that refreshed work triage preserves scope and cannot invent readiness."""
import copy
import unittest

from refresh_command_queue import refresh


class QueueRefreshTests(unittest.TestCase):
    def setUp(self):
        self.queue = {
            'source': {'ledger_sha256': 'same-ledger'},
            'counts': {'ready_unclaimed_source_programs': 0},
            'priority_ready_source_ids': [],
            'command_audit': [{
                'source_id': 'A', 'reproduce_command': 'python original.py',
                'source_evidence': [{'path': 'original.py', 'sha256': 'pinned'}],
                'ledger_status': 'negative', 'ledger_control': 'passed',
                'disposition': 'record-overlap-or-partial',
                'runnable_method': 'Historical note says not yet replayed.',
            }],
        }
        self.review = {
            'source': {'ledger_sha256': 'same-ledger'}, 'compiled': '2026-10-24',
            'entries': [{
                'source_id': 'A', 'status': 'partial',
                'record_links': [{'record_id': 'test-a', 'covered_subclaim': 'Only the fixed grid.'}],
                'execution_replay': {'state': 'complete-executed-grid', 'record_ids': ['test-a'],
                                     'scope': 'The executable grid, not every method variant.'},
                'unresolved_parts': ['Other keys were not tested.'],
                'whole_entry_coverage_verified': False,
            }],
        }
        self.records = [{'id': 'test-a', 'status': 'published'}]

    def run_refresh(self):
        return refresh(self.queue, self.review, self.records, 'review-hash')

    def test_current_evidence_separate_from_initial_assessment(self):
        before = copy.deepcopy(self.queue)
        updated = self.run_refresh()
        row = updated['command_audit'][0]
        self.assertEqual(self.queue, before)
        self.assertEqual(row['initial_assessment']['runnable_method'],
                         'Historical note says not yet replayed.')
        self.assertNotIn('runnable_method', row)
        self.assertEqual(row['reproduce_command'], 'python original.py')
        self.assertEqual(row['current_review']['record_links'], self.review['entries'][0]['record_links'])
        self.assertEqual(row['current_review']['remaining_scope'], ['Other keys were not tested.'])
        self.assertFalse(row['current_review']['whole_entry_coverage_verified'])
        self.assertEqual(updated['priority_ready_source_ids'], [])
        self.assertEqual(updated['counts']['execution_replay_states'], {'complete-executed-grid': 1})
        self.assertEqual(updated, refresh(updated, self.review, self.records, 'review-hash'))

    def test_duplicate_or_missing_source_id_rejected(self):
        self.review['entries'].append(copy.deepcopy(self.review['entries'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.run_refresh()
        self.review['entries'] = []
        with self.assertRaisesRegex(ValueError, 'missing from current review'):
            self.run_refresh()

    def test_unpublished_record_rejected_on_both_evidence_paths(self):
        self.records[0]['status'] = 'draft'
        with self.assertRaisesRegex(ValueError, 'unpublished/missing'):
            self.run_refresh()
        self.review['entries'][0]['record_links'] = []
        with self.assertRaisesRegex(ValueError, 'unpublished/missing'):
            self.run_refresh()

    def test_different_source_ledger_rejected(self):
        self.review['source']['ledger_sha256'] = 'other-ledger'
        with self.assertRaisesRegex(ValueError, 'different source ledgers'):
            self.run_refresh()

    def test_execution_scope_without_record_ids_is_retained(self):
        self.review['entries'][0]['execution_replay'] = {
            'state': 'partial-execution', 'scope': 'Input extraction only; no target search.'}
        result = self.run_refresh()
        self.assertEqual(result['command_audit'][0]['current_review']['execution_replay'],
                         self.review['entries'][0]['execution_replay'])
        self.assertEqual(result['priority_ready_source_ids'], [])


if __name__ == '__main__':
    unittest.main()
