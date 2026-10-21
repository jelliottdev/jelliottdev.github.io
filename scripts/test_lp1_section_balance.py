"""Exhaustive small fixtures for the constrained expectation and slot rules."""
from fractions import Fraction
from itertools import permutations,product
import unittest
from lp1_section_balance import expected_score,score

class ExpectedScore(unittest.TestCase):
    def test_exhaustive_section_orders(self):
        fixtures=[([[1,3,2],[4,6,1]],2),([[1],[2,3,4]],2),
            ([[1,1],[2,4]],2),([[3,3,3],[3,3,3]],2),([[1,4],[3],[2,5,1]],3)]
        for groups,k in fixtures:
            total=0;n=0
            for orders in product(*(list(permutations(g)) for g in groups)):
                values=sum((list(x) for x in orders),[])
                # Independent variance definition around the fixed mean of column means.
                means=[Fraction(sum(values[j::k]),len(values)//k) for j in range(k)]
                average=sum(means)/k
                variance=sum((x-average)**2 for x in means)/k
                q=variance*k**3*(len(values)//k)**2
                self.assertEqual(q,score(values,k));total+=q;n+=1
            expectation,counts,_,_=expected_score(groups,k)
            self.assertEqual(Fraction(total,n),expectation)
            self.assertEqual([sum(c) for c in counts],list(map(len,groups)))
    def test_boundary_does_not_reset_column(self):
        _,counts,_,_=expected_score([[1,3,2],[4,6,1]],2)
        self.assertEqual(counts,[[2,1],[1,2]])

if __name__=='__main__':unittest.main()
