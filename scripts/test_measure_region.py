"""Small deterministic checks for pixel measurements; Pillow is optional."""
import unittest
from measure_region import component_records


class RegionMeasurement(unittest.TestCase):
    def test_connectivity_and_area_filter(self):
        pixels = {(0, 0), (1, 1), (2, 2)}
        four, discarded = component_records(pixels, 4, 1)
        self.assertEqual([r['area_pixels'] for r in four], [1, 1, 1])
        self.assertEqual(discarded, 0)
        eight, discarded = component_records(pixels, 8, 3)
        self.assertEqual(eight, [{'area_pixels': 3, 'bounds': [0, 0, 3, 3], 'centroid': [1.0, 1.0]}])
        self.assertEqual(component_records(pixels, 4, 2), ([], 3))
        self.assertEqual(pixels, {(0, 0), (1, 1), (2, 2)})

    def test_original_coordinates_and_asymmetric_centroid(self):
        records, discarded = component_records({(100, 200), (101, 200), (100, 201), (900, 800)}, 8, 2)
        self.assertEqual(discarded, 1)
        self.assertEqual(records, [{'area_pixels': 3, 'bounds': [100, 200, 2, 2], 'centroid': [100.333333, 200.333333]}])

    def test_empty_and_invalid_rules(self):
        self.assertEqual(component_records(set()), ([], 0))
        for connectivity, area in [(6, 1), (8, 0)]:
            with self.assertRaises(ValueError):
                component_records(set(), connectivity, area)


if __name__ == '__main__':
    unittest.main()
