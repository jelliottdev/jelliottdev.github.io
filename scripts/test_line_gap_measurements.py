"""Independent original-pixel and export checks for the checked gap examples."""
import base64
import csv
import io
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

from build_line_gap_measurements import ROOT, build, measure


class GapMeasurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT/'exports/line-gap-measurements.json').read_text(encoding='utf8'))
        cls.rows = {r['id']: r for r in cls.data['rows']}

    def test_scope_and_rebuild(self):
        self.assertEqual(self.data, build())
        self.assertEqual(len(self.rows), 7)
        self.assertEqual(len({r['page'] for r in self.rows.values()}), 6)
        self.assertFalse(self.data['coverage']['complete_census'])
        self.assertEqual(sum(len(r['gaps']) for r in self.rows.values()), 52)
        self.assertEqual(len(self.rows['lp2-14']['source_records']), 2)

    def test_independent_histogram_edges_and_gap_rows(self):
        # Pillow histograms independently count thresholded pixels, without the
        # exporter's NumPy row reductions or active-row grouping implementation.
        for row in self.rows.values():
            gray = Image.open(ROOT/row['image_path']).convert('L')
            x0, y0, x1, y1 = row['rect_xyxy']
            for cutoff, result in row['measurements'].items():
                cutoff = int(cutoff)
                counts = {y: sum(gray.crop((x0,y,x1+1,y+1)).histogram()[:cutoff])
                          for y in range(y0,y1+1)}
                for line in result['lines']:
                    self.assertGreaterEqual(counts[line['top']], 5)
                    self.assertGreaterEqual(counts[line['bottom']], 5)
                    self.assertLess(counts[line['top']-1], 5)
                    self.assertLess(counts[line['bottom']+1], 5)
                active = [y for y,count in counts.items() if count >= 5]
                self.assertEqual(active[0], result['lines'][0]['top'])
                self.assertEqual(active[-1], result['lines'][-1]['bottom'])
                for gap in result['gaps']:
                    before = result['lines'][gap['from_line']-1]
                    after = result['lines'][gap['to_line']-1]
                    self.assertEqual(gap['top'], before['bottom']+1)
                    self.assertEqual(gap['bottom'], after['top']-1)
                    self.assertEqual(gap['pixels'], gap['bottom']-gap['top']+1)
                    self.assertTrue(all(counts[y] < 5 for y in range(gap['top'],gap['bottom']+1)))

    def test_clipped_row_correction_and_threshold_sensitive_panel(self):
        row = self.rows['lp2-35']
        self.assertEqual(row['rect_xyxy'], [580,630,1809,2950])
        self.assertEqual(row['lines'][-1], {'top':2779,'bottom':2893})
        self.assertEqual([g['pixels'] for g in row['gaps']], [74,75,74,110,74,74,73,73,74,73,73])
        panel = self.rows['lp2-15-panel']['measurements']
        self.assertEqual([g['pixels'] for g in panel['160']['gaps']], [62,61,79])
        self.assertEqual([g['pixels'] for g in panel['200']['gaps']], [61,60,78])

    def test_csv_complete_exact_join(self):
        with (ROOT/'exports/line-gap-measurements.csv').open(encoding='utf8',newline='') as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows),156)
        expected = {(r['id'],int(t),g['from_line']):g
                    for r in self.rows.values() for t,m in r['measurements'].items() for g in m['gaps']}
        seen = set()
        for row in rows:
            key = (row['region_id'],int(row['threshold']),int(row['from_line']))
            self.assertNotIn(key,seen)
            seen.add(key)
            self.assertEqual({k:int(row[k]) for k in expected[key]},expected[key])
            self.assertEqual([int(row['rect_'+k]) for k in ('x0','y0','x1','y1')],self.rows[key[0]]['rect_xyxy'])
        self.assertEqual(seen,set(expected))

    def test_embedded_crops_are_native_original_pixels(self):
        ns = {'s':'http://www.w3.org/2000/svg'}
        for row in self.rows.values():
            svg = ET.parse(ROOT/row['overlay_path']).getroot()
            images = svg.findall('s:g/s:image',ns)
            self.assertEqual(len(images),2)
            original = Image.open(ROOT/row['image_path']).convert('RGB')
            longest = max(row['gaps'],key=lambda g:g['pixels'])
            import statistics
            median = statistics.median(g['pixels'] for g in row['gaps'])
            typical = min((g for g in row['gaps'] if g is not longest),key=lambda g:(abs(g['pixels']-median),g['from_line']))
            for element,gap in zip(images,(longest,typical)):
                self.assertTrue(element.attrib['href'].startswith('data:image/png;base64,'))
                embedded = Image.open(io.BytesIO(base64.b64decode(element.attrib['href'].split(',',1)[1])))
                x0,_,x1,_ = row['rect_xyxy']
                top = row['lines'][gap['from_line']-1]['top']-10
                bottom = row['lines'][gap['to_line']-1]['bottom']+10
                expected = original.crop((x0,top,x1+1,bottom+1))
                self.assertEqual(embedded.size,expected.size)
                self.assertEqual(embedded.tobytes(),expected.tobytes())

    def test_minimum_ink_and_split_boundary(self):
        pixels = np.full((40,10),255,dtype=np.uint8)
        pixels[1,:4] = 0  # Four dark pixels do not activate a row.
        for y in (2,17,33):
            pixels[y,:5] = 0
        actual = measure(pixels,[0,0,9,39],160)
        self.assertEqual(actual['lines'],[{'top':2,'bottom':17},{'top':33,'bottom':33}])
        self.assertEqual(actual['gaps'],[{'from_line':1,'to_line':2,'top':18,'bottom':32,'pixels':15}])


if __name__ == '__main__':
    unittest.main()
