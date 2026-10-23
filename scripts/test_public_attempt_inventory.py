"""A suggested source match remains pending until its scope is reviewed."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import import_public_attempts as inventory


class ReviewAccounting(unittest.TestCase):
    def test_candidate_match_does_not_finish_review(self):
        ledger = json.dumps({'entries': [
            {'id': 'suggested-source'}, {'id': 'reviewed-source'}, {'id': 'unmatched-source'},
        ]}).encode()
        digest = hashlib.sha256(ledger).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'data').mkdir()
            (root / 'research').mkdir()
            (root / 'data/experiments.json').write_text(json.dumps({'records': [
                {'id': 'existing-record', 'article': 'Related to suggested-source.', 'sources': []},
            ]}), encoding='utf-8')
            (root / 'research/public-attempt-reconciliation.json').write_text(json.dumps({
                'source': {'ledger_sha256': digest},
                'entries': [{'source_id': 'reviewed-source', 'status': 'partial',
                             'whole_entry_coverage_verified': False}],
            }), encoding='utf-8')
            with patch.object(inventory, 'EXPECTED_SHA', digest):
                result = inventory.build(root, ledger)
        counts = result['counts']
        self.assertEqual(counts['source_entries_reviewed'], 1)
        self.assertEqual(counts['source_entries_pending_review'], 2)
        self.assertEqual(counts['pending_review_with_candidate_match'], 1)
        self.assertEqual(counts['pending_review_without_candidate_match'], 1)
        self.assertEqual(counts['verified_coverage'], 0)
        self.assertEqual(next(row for row in result['entries']
                              if row['source_id'] == 'suggested-source')['reconciliation_state'],
                         'candidate-overlap')


if __name__ == '__main__':
    unittest.main()
