import itertools
from collections import Counter
from fractions import Fraction
import unittest
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from rune_lag_matches import lag_counts, report


class LagMatches(unittest.TestCase):
    def test_all_lags_partition_the_ioc_pairs(self):
        for length in range(2, 7):
            for symbols in itertools.product('ABC', repeat=length):
                rows = lag_counts(symbols, length - 1)
                matches = sum(row['matching_pairs'] for row in rows)
                pairs = sum(row['compared_pairs'] for row in rows)
                frequencies = Counter(symbols)
                self.assertEqual(pairs, length * (length - 1) // 2)
                self.assertEqual(2 * matches, sum(c * (c - 1) for c in frequencies.values()))

    def test_saved_json_and_no_overwrite(self):
        script = Path(__file__).with_name('rune_lag_matches.py')
        command = [sys.executable, str(script), 'lp2-31', '--max-lag', '4']
        expected = subprocess.run(command, capture_output=True, check=True).stdout
        self.assertEqual(json.loads(expected)['rows'][1]['matching_pairs'], 9)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'report.json'
            subprocess.run([*command, '--output', str(output)], capture_output=True, check=True)
            self.assertEqual(output.read_bytes(), expected)
            failed = subprocess.run([*command, '--output', str(output)], capture_output=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(output.read_bytes(), expected)
            invalid = Path(directory) / 'invalid.json'
            failed = subprocess.run([sys.executable, str(script), 'lp2-31', '--max-lag', '269',
                                     '--output', str(invalid)], capture_output=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse(invalid.exists())

    def test_hand_example_without_wraparound(self):
        self.assertEqual(lag_counts('ABABA', 4), [
            {'lag': 1, 'matching_pairs': 0, 'compared_pairs': 4},
            {'lag': 2, 'matching_pairs': 3, 'compared_pairs': 3},
            {'lag': 3, 'matching_pairs': 0, 'compared_pairs': 2},
            {'lag': 4, 'matching_pairs': 1, 'compared_pairs': 1}])

    def test_expected_rate_over_every_distinct_shuffle(self):
        arrangements = set(itertools.permutations('AABB'))
        for lag in range(1, 4):
            rates = [Fraction(lag_counts(a, 3)[lag-1]['matching_pairs'], 4-lag) for a in arrangements]
            self.assertEqual(sum(rates) / len(rates), Fraction(1, 3))

    def test_order_matters_but_symbol_names_do_not(self):
        self.assertNotEqual(lag_counts('AABB', 3), lag_counts('ABAB', 3))
        self.assertEqual(lag_counts('ABABA', 4), lag_counts('XYXYX', 4))
        self.assertEqual(lag_counts('ABBAA', 4), lag_counts('AABBA', 4))

    def test_invalid_lags(self):
        for lag in [0, -1, 4, 1.5, True]:
            with self.assertRaises(ValueError):
                lag_counts('AABB', lag)
        with self.assertRaises(ValueError):
            lag_counts('', 1)

    def test_archived_page_scope(self):
        result = report('lp2-31', 20)
        self.assertEqual(result['rune_count'], 269)
        self.assertEqual(result['shuffle_expected_rate_fraction'], str(Fraction(2376, 72092)))
        self.assertEqual([r['compared_pairs'] for r in result['rows']], list(range(268, 248, -1)))
        for row in result['rows']:
            self.assertLessEqual(row['matching_pairs'], row['compared_pairs'])


if __name__ == '__main__':
    unittest.main()
