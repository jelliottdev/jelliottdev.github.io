"""Export formatting and rejection controls using synthetic report metadata."""
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from export_corpus_symbols import render

class Exports(unittest.TestCase):
    def test_rejects_incomplete_mismatched_and_partial_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=Path(tmp)/'report.json';receipt=Path(tmp)/'receipt.json'
            report.write_text('{"complete":false}',encoding='utf-8')
            receipt.write_text('{}',encoding='utf-8')
            with self.assertRaises(ValueError):render(report,receipt)
            report.write_text('{"complete":true}',encoding='utf-8')
            receipt.write_text(json.dumps({'report_sha256':'wrong'}),encoding='utf-8')
            with self.assertRaises(ValueError):render(report,receipt)
            receipt.write_text(json.dumps({'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),
                'paths_checked':12,'distinct_blobs_checked':12}),encoding='utf-8')
            with self.assertRaises(ValueError):render(report,receipt)

    def test_presence_and_occurrences_stay_distinct(self):
        # Synthetic metadata exercises presentation only, not verification.
        with tempfile.TemporaryDirectory() as tmp:
            report=Path(tmp)/'report.json';receipt=Path(tmp)/'receipt.json'
            data={'complete':True,'specification':{'revision':'fixture'},'records':[],
                'summary':{'eligible_paths':{'entries':10,'with_outside_symbols':3,
                    'outside_occurrences':{'ᛂ':9},'outside_entry_presence':{'ᛂ':3}},
                    'short_paths':{'entries':0,'with_outside_symbols':0,
                    'outside_occurrences':{},'outside_entry_presence':{}}}}
            data['summary']['eligible_distinct_blobs']=data['summary']['eligible_paths'].copy()
            data['summary']['short_distinct_blobs']=data['summary']['short_paths'].copy()
            report.write_text(json.dumps(data),encoding='utf-8')
            receipt.write_text(json.dumps({'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),
                'paths_checked':25906,'distinct_blobs_checked':25844}),encoding='utf-8')
            outputs=render(report,receipt)
            rows=list(csv.DictReader(io.StringIO(outputs['symbols.csv'])))
            self.assertEqual(len(rows),2)
            self.assertEqual(rows[0]['population_entries'],'10')
            self.assertEqual(rows[0]['entries_containing_symbol'],'3')
            self.assertEqual(rows[0]['symbol_occurrences'],'9')
            self.assertEqual(rows[0]['code_point'],'U+16C2')
            self.assertIn('short_paths,0,0,0\n',outputs['populations.csv'])
            self.assertNotIn('\r',outputs['symbols.csv'])
            self.assertIn('3 / 10 entries (30.00%)',outputs['coverage.svg'])
            self.assertEqual(outputs['coverage.svg'].count('No entries in this population'),2)

if __name__=='__main__':unittest.main()
