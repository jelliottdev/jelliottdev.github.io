"""Check suite attachment integrity and hash-refresh boundaries."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from build_experiments import validate_batch
from refresh_experiment_hashes import refresh


class SuiteRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case = dict(id='ciphertext-lag01-primer00-continuous', mode='ciphertext',
                         lag=1, primer=0, boundary='continuous', comparison_count=9,
                         opening_matches=[], max_prefix_length=0, decode_sha256='0' * 64)
        self.payload = dict(schema='liberpedia-feedback-opening-cases-v1', suite_id='demo', cases=[self.case])
        (self.root / 'manifest.json').write_text(json.dumps({'suite_id': 'demo'}))
        self.save_cases()
        self.record = dict(batch=dict(suite_id='demo', manifest_path='manifest.json',
                                     cases_path='cases.json', case_count=1, scope_note='Fixed demo scope'),
                           reproduction=dict(inputs=[{'path': 'manifest.json'}], outputs=[{'path': 'cases.json'}]))

    def save_cases(self):
        (self.root / 'cases.json').write_text(json.dumps(self.payload))

    def test_valid_attachment_and_count_drift(self):
        validate_batch(self.root, self.record)
        self.record['batch']['case_count'] = 2
        with self.assertRaisesRegex(ValueError, 'count mismatch'):
            validate_batch(self.root, self.record)

    def test_duplicate_cases_and_unpinned_output_rejected(self):
        self.payload['cases'].append(copy.deepcopy(self.case))
        self.record['batch']['case_count'] = 2
        self.save_cases()
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            validate_batch(self.root, self.record)
        self.record['reproduction']['outputs'] = []
        with self.assertRaisesRegex(ValueError, 'hashed output'):
            validate_batch(self.root, self.record)

    def test_hash_refresh_does_not_execute_or_change_review(self):
        folder = self.root / 'experiments/records/demo'
        folder.mkdir(parents=True)
        (folder / 'run.py').write_text('raise RuntimeError("Must not execute")\n')
        record = dict(id='demo', review={'human_review': 'pending'}, reproduction={
            'script': 'experiments/records/demo/run.py', 'script_sha256': '',
            'inputs': [{'path': 'manifest.json', 'sha256': ''}],
            'outputs': [{'path': 'cases.json', 'sha256': ''}]})
        path = folder / 'record.json'
        path.write_text(json.dumps(record))
        self.assertEqual(len(refresh(self.root, 'demo')), 3)
        self.assertEqual(json.loads(path.read_text()), record)
        refresh(self.root, 'demo', write=True)
        self.assertFalse(refresh(self.root, 'demo'))
        self.assertEqual(json.loads(path.read_text())['review'], record['review'])
        with self.assertRaises(ValueError):
            refresh(self.root, '../demo')


if __name__ == '__main__':
    unittest.main()
