"""Independent small examples and pinned historical-summary reconstruction."""
import csv
from fractions import Fraction
import json
from pathlib import Path
import unittest

from corpus_prefix_statistics import prefix, summarize, tails

ROOT = Path(__file__).resolve().parents[1]


class Conventions(unittest.TestCase):
    def test_literal_spaces_and_unicode_units(self):
        # U+16C2 is retained; newline is a counted code point, not a separator.
        self.assertEqual(prefix('ᚦ  ᛂ\n ᛁᛁ tail'.encode(), 3), [1,2,2])
        self.assertIsNone(prefix(b'a b', 3))

    def test_hand_calculated_sample_variance_and_quantiles(self):
        r = summarize([1,2,4,9])
        self.assertEqual(r['mean'],4)
        self.assertAlmostEqual(r['sample_variance'],float(Fraction(38,3)),places=12)
        self.assertEqual((r['percentile_25'],r['median'],r['percentile_75']),(1.75,3,5.25))

    def test_ties_and_file_weighting(self):
        self.assertEqual(tails([1,2,2,3],2),{'n':4,'less':1,'equal':2,'greater':1,'inclusive_left_numerator':3,'inclusive_right_numerator':3})
        self.assertEqual(tails([1,1,3],2)['inclusive_left_numerator'],2)
        with self.assertRaises(ValueError):tails([],2)

    def test_pinned_manuscript_summary(self):
        report=json.loads((ROOT/'exports/unsolved-word-lengths.json').read_bytes())
        histogram=report['runes_plus_single_digits']['histogram']
        values=[int(k) for k,n in histogram.items() for _ in range(n)]
        result=summarize(values)
        with (ROOT/'exports/sources/unsolved-word-length-summary.csv').open(newline='',encoding='utf-8') as file:
            original=next(csv.DictReader(file))
        names={'sample_variance':'var','sample_std':'std'}
        for name in ['mean','sample_variance','sample_std','median','percentile_25','percentile_75','min','max']:
            self.assertAlmostEqual(result[name],float(original[names.get(name,name)]),places=12)
        for name,value in original.items():
            if name.startswith('length_'):
                self.assertAlmostEqual(result['histogram'].get(name[7:],0)/result['tokens'],float(value),places=14)


if __name__ == '__main__': unittest.main()
