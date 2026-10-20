"""Small independent controls for the pair-count statistic."""
from itertools import product
import unittest
from rune_ioc import coincidence, report


class CoincidenceTests(unittest.TestCase):
    def test_edges(self):
        self.assertIsNone(coincidence("")["ioc"])
        self.assertIsNone(coincidence("F")["ioc"])
        self.assertEqual(coincidence("FF")["ioc"], 1)
        self.assertEqual(coincidence("FU")["ioc"], 0)
        self.assertAlmostEqual(coincidence("FFU")["ioc"], 1 / 3)

    def test_direct_pair_enumeration(self):
        # Independent oracle: enumerate unordered pairs rather than frequencies.
        for n in range(2, 7):
            for text in product("ABC", repeat=n):
                matches = sum(text[i] == text[j] for i in range(n) for j in range(i))
                self.assertEqual(coincidence(text)["ioc"], matches / (n * (n - 1) / 2))

    def test_invariants(self):
        text = "AAABBCD"
        self.assertEqual(coincidence(text), coincidence(text[::-1]))
        self.assertEqual(coincidence(text), coincidence(text.translate(str.maketrans("ABCD", "WXYZ"))))

    def test_archive(self):
        records = report()["records"]
        self.assertEqual(len(records), 75)
        for record in records:
            self.assertEqual(sum(record["counts"]), record["n"])
            if record["n"] < 2:
                self.assertIsNone(record["ioc"])
            else:
                self.assertTrue(0 <= record["ioc"] <= 1)


if __name__ == "__main__":
    unittest.main()
