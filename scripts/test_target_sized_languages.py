"""Focused controls for units, exact distances and ties."""
import unittest
from fractions import Fraction
from check_target_sized_languages import lengths, histogram, score


class TargetSizedControls(unittest.TestCase):
    def test_unicode_boundary_is_explicit(self):
        self.assertEqual(lengths('\u0130zmir','letters'),[1,4])
        self.assertEqual(lengths('\u0130zmir','folded'),[5])
        self.assertEqual(lengths('\u0130zmir','gp-length'),[5])

    def test_apostrophes_hyphens_and_groups(self):
        self.assertEqual(lengths("can't l\u2019arbre co-op",'letters'),[4,6,2,2])
        self.assertEqual(lengths('thing singing','gp-length'),[2,3])
        self.assertEqual(lengths('123 ---','letters'),[])

    def test_exact_distance_and_tie(self):
        a=histogram([1,2]); b=histogram([1,1]); c=histogram([2,2])
        self.assertEqual(score(a,b),Fraction(1,2))
        self.assertEqual(score(a,b),score(a,c))
        self.assertEqual(score(b,c),1)
        self.assertEqual(score(a,[2*x for x in a]),0)
        self.assertEqual(histogram([16,17,100])[-1],3)


if __name__=='__main__':unittest.main()
