"""Exhaustive matching controls independent of image measurements."""
from itertools import product
import unittest
from image_row_coverage import maximum, overlaps


def enumerate_matchings(edges):
    def visit(row,used,pairs):
        if row==len(edges):
            yield frozenset(pairs);return
        yield from visit(row+1,used,pairs)
        for band in edges[row]:
            if band not in used:
                yield from visit(row+1,used|{band},pairs+[(row,band)])
    choices=list(visit(0,set(),[]));size=max(map(len,choices))
    return size,[c for c in choices if len(c)==size]


class Matching(unittest.TestCase):
    def test_every_three_by_three_graph(self):
        for bits in product([False,True],repeat=9):
            edges=[[j for j in range(3) if bits[3*i+j]] for i in range(3)]
            size,choices=enumerate_matchings(edges)
            self.assertEqual(maximum(edges),size)
            for i in range(3):
                self.assertEqual(maximum(edges,i)<size,all(any(row==i for row,_ in c) for c in choices))
                for j in edges[i]:
                    self.assertEqual(1+maximum(edges,i,j)==size,any((i,j) in c for c in choices))

    def test_half_open_and_iou_threshold(self):
        self.assertFalse(overlaps([0,10],[10,20]))
        self.assertTrue(overlaps([0,10],[0,20]))
        self.assertFalse(overlaps([0,10],[0,21]))
        self.assertTrue(overlaps([0,10],[0,10]))


if __name__=='__main__':unittest.main()
