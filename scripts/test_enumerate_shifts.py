import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from enumerate_shifts import candidates, report, ROOT


class ShiftEnumeration(unittest.TestCase):
    def test_hand_calculated_order_and_subtraction(self):
        cases = candidates([0, 1, 28])
        self.assertEqual(len(cases), 58)
        self.assertEqual(cases[1], {"order": "original", "shift": 1, "indices": [28, 0, 27]})
        self.assertEqual(cases[30], {"order": "reversed", "shift": 1, "indices": [27, 0, 28]})
        self.assertEqual(cases[28]["indices"], [1, 2, 0])
        self.assertEqual(len({(c["order"], c["shift"]) for c in cases}), 58)

    def test_cases_need_not_be_distinct(self):
        cases = candidates([0, 0])
        self.assertEqual(len({tuple(c["indices"]) for c in cases}), 29)

    def test_invalid_inputs(self):
        for value in [[], [-1], [29], [True], [1.5]]:
            with self.assertRaises(ValueError):
                candidates(value)
        with self.assertRaises(ValueError):
            report("../lp2-31")

    def test_cli_saves_report_and_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "cases.json"
            command = [sys.executable, str(ROOT / "scripts/enumerate_shifts.py"),
                       "lp2-31", "--output", str(path)]
            subprocess.run(command, check=True, capture_output=True)
            saved = path.read_bytes()
            result = json.loads(saved)
            self.assertEqual(result["rune_count"], 269)
            self.assertEqual(result["source_sha256"],
                             "493cb51478b106dd626ff93625abaf10c9675ad221896b5206809041dfd55b68")
            self.assertTrue(all(len(c["indices"]) == 269 for c in result["cases"]))
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(path.read_bytes(), saved)


if __name__ == "__main__":
    unittest.main()
