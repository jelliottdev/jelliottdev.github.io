"""Regression checks for the metadata used by download filters."""
import json
from pathlib import Path
import unittest

from check_download_catalog import verify_scopes

ROOT = Path(__file__).resolve().parents[1]


class DownloadScopeTests(unittest.TestCase):
    def setUp(self):
        self.records = json.loads((ROOT / 'data/catalog.json').read_text(encoding='utf-8'))['files']

    def record(self, path):
        return next(item for item in self.records if item['path'] == path)

    def test_current_metadata_matches_source_records(self):
        self.assertEqual(verify_scopes(ROOT, self.records), [])

    def test_missing_page_is_detected(self):
        self.record('exports/rune-ioc.csv')['pages'].pop()
        self.assertTrue(any('page scope' in error for error in verify_scopes(ROOT, self.records)))

    def test_wrong_release_is_detected(self):
        self.record('exports/known-reading-page-sums.csv')['releases'] = ['LP2']
        self.assertTrue(any('release scope' in error for error in verify_scopes(ROOT, self.records)))

    def test_grid_script_needs_the_same_scope_as_its_output(self):
        self.record('scripts/export_alphanumeric_grids.py')['pages'] = ['lp2-49']
        self.assertTrue(any('export_alphanumeric_grids.py' in error for error in verify_scopes(ROOT, self.records)))

    def test_panel_source_determines_page(self):
        self.record('exports/lp2-15-differences.json')['page'] = 'lp2-31'
        self.assertTrue(any('number-panel source' in error for error in verify_scopes(ROOT, self.records)))

    def test_missing_catalog_entry_is_detected(self):
        self.records.remove(self.record('exports/alphanumeric-grids.csv'))
        self.assertTrue(any('exports/alphanumeric-grids.csv' in error for error in verify_scopes(ROOT, self.records)))

    def test_duplicate_scope_pages_are_detected(self):
        record = self.record('exports/rune-ioc.csv')
        record['pages'].append(record['pages'][0])
        self.assertTrue(any('page scope' in error for error in verify_scopes(ROOT, self.records)))


if __name__ == '__main__':
    unittest.main()
