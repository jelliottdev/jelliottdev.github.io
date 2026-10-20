import math
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from collections import Counter
from rune_entropy import entropy, report


class RuneEntropy(unittest.TestCase):
    def test_cli_saved_bytes_and_overwrite(self):
        command = [sys.executable, str(Path(__file__).with_name("rune_entropy.py")), "lp2-31"]
        printed = subprocess.run(command, capture_output=True, check=True).stdout
        self.assertEqual(json.loads(printed), report("lp2-31"))
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "entropy.json"
            subprocess.run(command + ["--output", str(output)], capture_output=True, check=True)
            self.assertEqual(output.read_bytes(), printed)
            refused = subprocess.run(command + ["--output", str(output)], capture_output=True)
            self.assertNotEqual(refused.returncode, 0)
            self.assertEqual(output.read_bytes(), printed)

    def test_hand_calculated_distributions(self):
        self.assertIsNone(entropy([0, 0]))
        self.assertEqual(entropy([8, 0]), 0)
        self.assertEqual(entropy([4, 4]), 1)
        self.assertEqual(entropy([2, 2, 2, 2]), 2)
        self.assertAlmostEqual(entropy([1] * 29), math.log2(29))
        self.assertAlmostEqual(entropy([3, 1]), 0.8112781244591328)

    def test_order_and_labels_cannot_be_detected(self):
        strings = ["AAAABBBB", "ABABABAB", "XXXXYYYY"]
        self.assertEqual([entropy(list(Counter(s).values())) for s in strings], [1, 1, 1])

    def test_invalid_counts(self):
        for counts in ([-1, 2], [True], [1.5]):
            with self.assertRaises(ValueError): entropy(counts)

    def test_page_scope_and_empty_page(self):
        row = report("lp2-31")
        self.assertEqual(row["n"], 269)
        self.assertEqual(sum(row["counts"]), 269)
        self.assertEqual(row["input_sha256"], "493cb51478b106dd626ff93625abaf10c9675ad221896b5206809041dfd55b68")
        self.assertIsNone(report("lp1-00")["empirical_entropy_bits"])
        with self.assertRaises(ValueError): report("../unknown")


if __name__ == "__main__": unittest.main()
