"""Prevent already reviewed source entries being counted as fresh queue work."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

path = Path(__file__).resolve().parents[1] / 'research/source-intake/select_pending.py'
spec = importlib.util.spec_from_file_location('pending_source_selection', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PendingSelectionTests(unittest.TestCase):
    def setUp(self):
        self.ledger = {'entries': [{'id': 'old', 'hypothesis': 'Old claim'}, {'id': 'new', 'hypothesis': 'New claim'}]}
        self.reviews = {'entries': [{'source_id': 'old', 'status': 'partial'}]}

    def test_partial_review_is_not_a_new_initial_review(self):
        self.assertEqual([r['source_id'] for r in module.select(self.ledger, self.reviews)], ['new'])

    def test_intentional_followup_is_explicit(self):
        with self.assertRaisesRegex(ValueError, 'Already reviewed'):
            module.select(self.ledger, self.reviews, ['old', 'new'])
        rows = module.select(self.ledger, self.reviews, ['old', 'new'], allow_reviewed=True)
        self.assertEqual([r['work_type'] for r in rows], ['follow-up', 'initial review'])

    def test_duplicate_or_unknown_source_ids_fail(self):
        for wanted in [['new', 'new'], ['unknown']]:
            with self.assertRaises(ValueError):
                module.select(self.ledger, self.reviews, wanted)
        with self.assertRaises(ValueError):
            module.select(self.ledger, {'entries': self.reviews['entries'] * 2})

    def test_cli_preserves_unicode_under_legacy_pipe_encoding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = json.dumps({'entries': [{'id': 'new', 'hypothesis': 'A \u2192 B'}]}).encode()
            (root / 'ledger.json').write_bytes(ledger)
            (root / 'reviews.json').write_text(json.dumps({
                'source': {'ledger_sha256': hashlib.sha256(ledger).hexdigest()},
                'entries': [],
            }), encoding='utf-8')
            result = subprocess.run([
                sys.executable, str(path), '--ledger', str(root / 'ledger.json'),
                '--reconciliation', str(root / 'reviews.json'),
            ], env={**os.environ, 'PYTHONIOENCODING': 'cp1252'}, capture_output=True, check=True)
            self.assertEqual(json.loads(result.stdout)['entries'][0]['claim'], 'A \u2192 B')


if __name__ == '__main__':
    unittest.main()
