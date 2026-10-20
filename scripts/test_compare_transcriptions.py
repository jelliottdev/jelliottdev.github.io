"""Checks for lost runes, shifted locations and representation differences."""
import tempfile
import unittest
from pathlib import Path
from compare_transcriptions import compare


class ComparisonTests(unittest.TestCase):
    def report(self, left, right):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / 'a.txt', Path(folder) / 'b.txt'
            a.write_bytes(left.encode('utf-8'))
            b.write_bytes(right.encode('utf-8'))
            return compare(a, b, ['ᚠ', 'ᚢ', 'ᚦ'])

    def test_identical(self):
        r = self.report('ᚠ-ᚢ', 'ᚠ-ᚢ')
        self.assertTrue(r['bytes_equal'])
        self.assertEqual(r['text_changes'], [])
        self.assertEqual(r['rune_changes'], [])

    def test_format_only_preserves_raw_bytes(self):
        r = self.report('\ufeffᚠ-ᚢ\r\n', 'ᚠ ᚢ\n')
        self.assertFalse(r['bytes_equal'])
        self.assertTrue(r['runes_equal'])
        self.assertTrue(r['text_changes'])
        self.assertIn('\r', r['inputs'][0]['non_rune_counts'])

    def test_substitution_location(self):
        r = self.report('ᚠ-\nᚢ', 'ᚠ-\nᚦ')
        change = r['rune_changes'][0]
        self.assertEqual(change['left_range'], [1, 2])
        self.assertEqual(change['left_positions'], [{'source_offset': 3, 'line': 2, 'column': 1}])
        self.assertEqual(change['right_text'], 'ᚦ')

    def test_insertion_and_deletion(self):
        for a, b, operation in [('ᚠᚢ', 'ᚠᚦᚢ', 'insert'), ('ᚠᚦᚢ', 'ᚠᚢ', 'delete')]:
            r = self.report(a, b)
            self.assertEqual(r['rune_changes'][0]['operation'], operation)

    def test_unknown_rune_fails(self):
        with self.assertRaises(ValueError):
            self.report('ᚠ', 'ᚡ')

    def test_empty_and_non_runes_are_visible(self):
        r = self.report('', 'ABC123')
        self.assertTrue(r['runes_equal'])
        self.assertEqual(r['inputs'][1]['runes'], 0)
        self.assertEqual(r['text_changes'][0]['right_text'], 'ABC123')


if __name__ == '__main__':
    unittest.main()
