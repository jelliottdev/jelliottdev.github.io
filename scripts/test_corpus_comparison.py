"""Small independent arithmetic controls; not a full-corpus audit."""
from collections import Counter
from fractions import Fraction
import itertools
import statistics
import unittest

from compare_corpus_prefixes import exact_profile, rank_profiles
from check_corpus_comparison import expanded_profile, check_rows


class ComparisonControls(unittest.TestCase):
    def test_hand_values_and_long_bin(self):
        p = exact_profile({'1': 1, '2': 1, '4': 1, '9': 1})
        self.assertEqual(len(p), 23)
        self.assertEqual(p['mean'], 4)
        self.assertEqual(p['sample_variance'], Fraction(38, 3))
        self.assertEqual(p['sample_std'], Fraction(38, 3))  # Comparison scale, not sqrt.
        self.assertEqual([p[k] for k in ('percentile_25', 'median', 'percentile_75')],
                         [Fraction(7, 4), 3, Fraction(21, 4)])
        self.assertEqual(exact_profile({'14': 1, '15': 1, '100': 2})['length_15_plus'], Fraction(3, 4))

    def test_ties_and_duplicate_weights(self):
        one, two, three = [exact_profile({str(k): 4}) for k in (1, 2, 3)]
        weighted = {r['measure']: r for r in rank_profiles([one, two, two, three], two)}['mean']
        self.assertEqual([weighted[k] for k in ('below', 'equal', 'above')], [1, 2, 1])
        self.assertEqual(weighted['inclusive_left_numerator'], 3)
        self.assertEqual(weighted['inclusive_right_numerator'], 3)
        unique = {r['measure']: r for r in rank_profiles([one, two, three], two)}['mean']
        self.assertEqual(unique['reference_count'], 3)
        self.assertEqual(unique['inclusive_left_numerator'], 2)

    def test_against_expanded_exact_statistics(self):
        for values in itertools.product((1, 3, 16), repeat=4):
            p = exact_profile({str(k): v for k, v in Counter(values).items()})
            exact = [Fraction(x) for x in values]
            self.assertEqual(p['mean'], statistics.mean(exact))
            self.assertEqual(p['sample_variance'], statistics.variance(exact))
            q = statistics.quantiles(exact, n=4, method='inclusive')
            self.assertEqual([p[k] for k in ('percentile_25', 'median', 'percentile_75')], q)

    def test_close_fractions_do_not_become_ties(self):
        target = {'mean': Fraction(1)}
        rows = rank_profiles([{'mean': Fraction(10**20 - 1, 10**20)}, target,
                              {'mean': Fraction(10**20 + 1, 10**20)}], target)
        self.assertEqual([rows[0][k] for k in ('below', 'equal', 'above')], [1, 1, 1])

    def test_independent_checker_and_corruptions(self):
        histograms = [{'1': 2, '3': 2}, {'2': 4}, {'1': 1, '2': 2, '16': 1}]
        producer = [exact_profile(h) for h in histograms]
        independent = [expanded_profile(h) for h in histograms]
        self.assertEqual(producer, independent)
        rows = rank_profiles(producer, producer[0])
        check_rows(rows, independent, independent[0])
        for key in ('below', 'equal', 'above', 'inclusive_left_numerator',
                    'inclusive_right_numerator', 'reference_count'):
            damaged = [dict(r) for r in rows]
            damaged[0][key] += 1
            with self.assertRaises(AssertionError):
                check_rows(damaged, independent, independent[0])
        with self.assertRaises(AssertionError):
            check_rows(rows[:-1], independent, independent[0])
        with self.assertRaises(AssertionError):
            check_rows(list(reversed(rows)), independent, independent[0])


if __name__ == '__main__':
    unittest.main()
