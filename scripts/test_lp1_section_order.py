"""Exhaustive finite checks for cyclic reduction; no manuscript inputs."""
from itertools import permutations,product
import unittest
from lp1_section_order import partition,class_scores,score

class CyclicOrders(unittest.TestCase):
    def test_all_small_section_permutations(self):
        orders,reps,membership=partition()
        for original in [[[1],[2],[3],[4]],[[1],[3,2],[4],[1,5]],[[1],[1,2,4],[2,2],[3,5]]]:
            for options in product(*(list(permutations(g)) for g in original)):
                groups=[list(g) for g in options]
                reduced=class_scores(groups,2,reps)
                for i,order in enumerate(orders):
                    values=[v for s in order for v in groups[s]]
                    sums=[sum(v for j,v in enumerate(values) if j%2==c) for c in range(2)]
                    q=4*sum(x*x for x in sums)-2*sum(values)**2
                    self.assertEqual(q,reduced[membership[i]])
    def test_nondivisible_counterexample(self):
        self.assertEqual(score([1,2,4],2),18)
        self.assertEqual(score([2,4,1],2),2)
        with self.assertRaises(AssertionError):class_scores([[1],[2],[3],[4,5]],2,partition()[1])

if __name__=='__main__':unittest.main()
