import unittest
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from rune_ngrams import repeated_windows, report, indexed_runes, occurrence, ROOT


class RuneNgrams(unittest.TestCase):
    def test_cli_utf8_output_matches_saved_file_and_refuses_overwrite(self):
        command = [sys.executable, str(ROOT / "scripts/rune_ngrams.py"), "lp2-31", "--length", "2"]
        environment = dict(os.environ, PYTHONIOENCODING="ascii")
        printed = subprocess.run(command, capture_output=True, env=environment, check=True).stdout
        decoded = printed.decode("utf-8")
        self.assertIn("ᚱᛖ", decoded)
        self.assertNotIn("\\u16", decoded)
        self.assertNotIn(b"\r\n", printed)
        self.assertEqual(json.loads(decoded), report("lp2-31", 2))
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "report.json"
            subprocess.run(command + ["--output", str(output)], capture_output=True,
                           env=environment, check=True)
            self.assertEqual(output.read_bytes(), printed)
            refused = subprocess.run(command + ["--output", str(output)], capture_output=True)
            self.assertNotEqual(refused.returncode, 0)
            self.assertEqual(output.read_bytes(), printed)

    def test_source_positions_preserve_separators_and_unicode_characters(self):
        text = "🙂ᚠ-/\r\nᚢ.ᚠ"
        symbols, positions = indexed_runes(text, {"ᚠ": 0, "ᚢ": 1})
        self.assertEqual(symbols, [0, 1, 0])
        self.assertEqual(occurrence(text, positions, 0, 2),
                         {"start_rune": 0, "source_start": 1, "source_end": 7,
                          "source_line": 1, "source_column": 2,
                          "source_text": "ᚠ-/\r\nᚢ"})
        self.assertEqual(positions[1], {"offset": 6, "line": 2, "column": 1})

    def test_report_occurrences_recover_exact_source_slices(self):
        result = report("lp2-31", 2)
        source = (ROOT / result["source"]).read_bytes().decode("utf-8")
        alphabet = set("ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ")
        for pattern in result["patterns"]:
            self.assertEqual(len(pattern["occurrences"]), pattern["count"])
            for item in pattern["occurrences"]:
                self.assertEqual(source[item["source_start"]:item["source_end"]],
                                 item["source_text"])
                self.assertEqual("".join(c for c in item["source_text"] if c in alphabet),
                                 pattern["runes"])
                self.assertEqual(source.count("\n", 0, item["source_start"]) + 1,
                                 item["source_line"])

    def test_report_carries_its_own_index_mapping(self):
        result = report("lp2-31", 2)
        alphabet = result["alphabet"]
        self.assertEqual(len(alphabet), 29)
        self.assertEqual(len(set(alphabet)), 29)
        self.assertEqual(hashlib.sha256("".join(alphabet).encode("utf-8")).hexdigest(),
                         result["alphabet_sha256"])
        for pattern in result["patterns"]:
            self.assertEqual("".join(alphabet[i] for i in pattern["indices"]),
                             pattern["runes"])
        # The mapping must still be present when no repeated patterns are found.
        self.assertEqual(report("lp2-31", 3)["alphabet"], alphabet)

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
