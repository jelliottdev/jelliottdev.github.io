import json
import unittest
from reading_concordance import SOURCE, concordance


class ReadingConcordance(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
