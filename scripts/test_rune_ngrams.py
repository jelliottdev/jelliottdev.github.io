import unittest
from rune_ngrams import repeated_windows, report


class RuneNgrams(unittest.TestCase):
    def test_overlapping_windows(self):
        self.assertEqual(repeated_windows([0, 0, 0, 0], 2), [((0, 0), [0, 1, 2])])
        self.assertEqual(repeated_windows([0, 1, 0, 1, 0], 3), [((0, 1, 0), [0, 2])])

    def test_short_stream_and_single_occurrence(self):
        self.assertEqual(repeated_windows([], 3), [])
        self.assertEqual(repeated_windows([0, 1], 3), [])
        self.assertEqual(repeated_windows([0, 1, 2], 2), [])

    def test_count_then_alphabet_order(self):
        self.assertEqual(repeated_windows([2, 1, 2, 1, 0, 0, 0], 1),
                         [((0,), [4, 5, 6]), ((1,), [1, 3]), ((2,), [0, 2])])

    def test_invalid_length_and_page(self):
        for length in [0, -1, 13, True, 2.5]:
            with self.assertRaises(ValueError):
                repeated_windows([0, 1], length)
        with self.assertRaises(ValueError):
            report("../outside", 3)


if __name__ == "__main__":
    unittest.main()
