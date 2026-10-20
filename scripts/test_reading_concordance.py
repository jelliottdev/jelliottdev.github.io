import json
import unittest
import subprocess
import sys
import tempfile
from pathlib import Path
from reading_concordance import ROOT, SOURCE, concordance, literal_concordance


class ReadingConcordance(unittest.TestCase):
    def test_saved_reports_match_stdout_and_preserve_existing_files(self):
        script = Path(__file__).with_name("reading_concordance.py")
        with tempfile.TemporaryDirectory() as folder:
            for flags, extension in [([], "txt"), (["--json"], "json"),
                                     (["--literal", "--json"], "literal.json")]:
                output = Path(folder) / ("result." + extension)
                command = [sys.executable, str(script), "circumference", "--prefix", *flags]
                expected = subprocess.run(command, capture_output=True, check=True).stdout
                subprocess.run([*command, "--output", str(output)],
                               capture_output=True, check=True)
                self.assertEqual(output.read_bytes(), expected)
                refused = subprocess.run([*command, "--output", str(output)],
                                         capture_output=True)
                self.assertNotEqual(refused.returncode, 0)
                self.assertEqual(output.read_bytes(), expected)
                if extension == "json":
                    self.assertEqual(json.loads(expected)["occurrences"], 3)
            invalid = Path(folder) / "invalid.json"
            failed = subprocess.run([sys.executable, str(script), "two words",
                                     "--prefix", "--output", str(invalid)], capture_output=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse(invalid.exists())

    def test_published_circumference_passages(self):
        controls = json.loads(SOURCE.read_bytes())["controls"]
        self.assertEqual(len(controls), 9)
        exact = concordance(controls, "circumference")
        self.assertEqual([(h["section"], h["word_start"]) for h in exact],
                         [("loss-of-divinity", 6), ("second-koan", 18)])
        expanded = concordance(controls, "circumference", prefix=True)
        self.assertEqual([(h["section"], h["matched"]) for h in expanded],
                         [("loss-of-divinity", "CIRCUMFERENCE"),
                          ("second-koan", "CIRCUMFERENCE"),
                          ("lp2-57", "CIRCUMFERENCES")])
        self.assertEqual(expanded[0]["section_pages"], ["lp1-10", "lp1-11", "lp1-12", "lp1-13"])

    def test_literal_pages_and_original_wraps(self):
        hits, sources = literal_concordance(ROOT, "circumference", prefix=True)
        self.assertEqual(len(sources), 17)
        self.assertEqual([(h["page"], h["line_start"], h["line_end"]) for h in hits],
                         [("lp1-10", 1, 2), ("lp1-14", 3, 4), ("lp2-57", 3, 4)])
        self.assertEqual(hits[0]["matched_source"], "CIRCU/\nMFERENCE")
        for hit in hits:
            literal = json.loads((ROOT / hit["source"]).read_bytes())["reading"]["literal"]
            self.assertEqual(literal[hit["source_start"]:hit["source_end"]],
                             hit["matched_source"])
            self.assertIn(hit["matched_source"], hit["source_excerpt"])

    def test_literal_search_preserves_spelling_and_page_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "data/pages"
            folder.mkdir(parents=True)
            for page, literal in [("a", "☀ DIUINITY.SELF"),
                                  ("b", "KNOWLEDGE.CIRCU/\r\nMFERENCE")]:
                (folder / (page + ".json")).write_text(
                    json.dumps({"id": page, "reading": {"literal": literal}}), encoding="utf-8")
            self.assertEqual(literal_concordance(root, "divinity")[0], [])
            self.assertEqual(len(literal_concordance(root, "diuinity")[0]), 1)
            self.assertEqual(literal_concordance(root, "self knowledge")[0], [])
            hit = literal_concordance(root, "circumference", context=0)[0][0]
            self.assertEqual(hit["matched_source"], "CIRCU/\r\nMFERENCE")
            self.assertEqual(hit["source_excerpt"], hit["matched_source"])
            self.assertEqual((hit["line_start"], hit["line_end"]), (1, 2))

    def test_phrase_boundaries_and_apostrophes(self):
        controls = [{"id": "a", "pages": ["a"], "reading": "Don't stop. SELF"},
                    {"id": "b", "pages": ["b"], "reading": "KNOWLEDGE don't STOP"}]
        self.assertEqual(len(concordance(controls, "DON’T stop")), 2)
        self.assertEqual(concordance(controls, "self knowledge"), [])
        self.assertEqual(concordance(controls, "stop", context=0)[0]["before"], "")

    def test_rejects_ambiguous_or_invalid_inputs(self):
        for query, prefix, context in [("", False, 10), ("two words", True, 10),
                                       ("word", False, -1)]:
            with self.assertRaises(ValueError):
                concordance([], query, prefix, context)
        with self.assertRaises(ValueError):
            concordance([{"id": "same"}, {"id": "same"}], "word")

    def test_original_excerpt_and_character_positions(self):
        reading = "☀ Before: Don’t,\nSTOP! After."
        hit = concordance([{"id": "a", "pages": ["a"], "reading": reading}],
                          "don't stop", context=1)[0]
        self.assertEqual(hit["matched_source"], "Don’t,\nSTOP")
        self.assertEqual(hit["source_excerpt"], "Before: Don’t,\nSTOP! After")
        self.assertEqual(reading[hit["source_start"]:hit["source_end"]],
                         hit["matched_source"])
        self.assertEqual(hit["source_start"], 10)
        self.assertEqual((hit["word_start"], hit["word_end"]), (2, 3))
        zero = concordance([{"id": "a", "pages": [], "reading": reading}],
                           "stop", context=0)[0]
        self.assertEqual(zero["source_excerpt"], "STOP")


if __name__ == "__main__":
    unittest.main()
