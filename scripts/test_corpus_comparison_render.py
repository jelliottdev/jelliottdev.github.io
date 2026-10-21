"""Synthetic presentation controls; these are not manuscript results."""
import copy
import json
import unittest
import xml.etree.ElementTree as ET
from render_corpus_comparison import PLAN, render


class PresentationControls(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(PLAN.read_bytes())
        rows = []
        for i, measure in enumerate(self.plan['measures']):
            below, equal, above = [(10,0,0),(0,10,0),(0,0,10),(3,4,3)][i%4]
            rows.append(dict(measure=measure, comparison_scale='variance' if measure=='sample_std' else measure,
                             target_comparison_value={'numerator':9,'denominator':4},
                             reference_count=10, below=below, equal=equal, above=above,
                             inclusive_left_numerator=below+equal, inclusive_right_numerator=above+equal))
        self.data = {'comparisons': {w:copy.deepcopy(rows) for w in self.plan['weighting']}}

    def test_all_rows_and_ties_remain_visible(self):
        svg, md = render(self.data, self.plan)
        root = ET.fromstring(svg)
        ns = {'s':'http://www.w3.org/2000/svg'}
        bars = [r for r in root.findall('s:rect', ns) if r.find('s:title', ns) is not None]
        self.assertEqual(len(bars),46*3)
        for i in range(0,len(bars),3):
            self.assertAlmostEqual(sum(float(r.attrib['width']) for r in bars[i:i+3]),220)
        self.assertEqual(len([line for line in md.splitlines() if line.startswith('| ')]),50)
        self.assertIn('| Length 2 | 9/4 | 0 | 10 | 0 | 10/10 | 10/10 |',md)
        self.assertIn('not calibrated p-values',svg)

    def test_std_display_is_not_its_ranking_variance(self):
        _, md = render(self.data, self.plan)
        self.assertIn('| Variance | 9/4 |', md)
        self.assertIn('| Standard deviation | √(9/4) |', md)

    def test_rejects_invalid_target_fraction(self):
        self.data['comparisons'][self.plan['weighting'][0]][0]['target_comparison_value']['denominator'] = 0
        with self.assertRaises(AssertionError):render(self.data,self.plan)

    def test_rejects_missing_measure(self):
        self.data['comparisons'][self.plan['weighting'][0]].pop()
        with self.assertRaises(AssertionError):render(self.data,self.plan)

    def test_rejects_complement_substitution(self):
        row=self.data['comparisons'][self.plan['weighting'][0]][1]
        row['inclusive_right_numerator']=0
        with self.assertRaises(AssertionError):render(self.data,self.plan)

    def test_rejects_wrong_std_scale(self):
        for row in self.data['comparisons'][self.plan['weighting'][0]]:
            if row['measure']=='sample_std':row['comparison_scale']='sample_std'
        with self.assertRaises(AssertionError):render(self.data,self.plan)


if __name__=='__main__':unittest.main()
