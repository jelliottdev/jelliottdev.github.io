"""Check correction and withdrawal behavior with isolated synthetic page records."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from build_page_notes import apply_notes, SOURCE


class EditorialNotes(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.digest = hashlib.sha256(b"fixture image bytes").hexdigest()
        self.archive = {"title": "Archive note", "text": "Preserve this measurement."}
        self.record = {"page": "lp2-33", "image_sha256": self.digest,
                       "notes": [{"title": "Editorial note", "text": "An observation.", "rect": [1, 2, 3, 4]}]}
        self.save("data/index.json", {"pages": [{"id": "lp2-33", "notes_text": "Archive note Preserve this measurement."}]})
        self.save("data/pages/lp2-33.json", {"notes": [self.archive], "image_sha256": self.digest, "image_dimensions": [10, 10]})
        (self.root / "images").mkdir()
        (self.root / "images/lp2-33.jpg").write_bytes(b"fixture image bytes")
        self.save(SOURCE, {"records": [self.record]})

    def save(self, path, value):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(value), encoding="utf-8")

    def outputs(self):
        return [(self.root / p).read_bytes() for p in ["data/index.json", "data/pages/lp2-33.json"]]

    def test_repeat_and_withdrawal_preserve_archive_notes(self):
        apply_notes(self.root)
        saved = self.outputs()
        apply_notes(self.root)
        self.assertEqual(self.outputs(), saved)
        self.save(SOURCE, {"records": []})
        apply_notes(self.root)
        page = json.loads(self.outputs()[1])
        self.assertEqual(page["notes"], [self.archive])
        self.assertNotIn("Editorial note", json.loads(self.outputs()[0])["pages"][0]["notes_text"])

    def test_invalid_evidence_never_changes_published_records(self):
        baseline = self.outputs()
        variants = []
        for rect in [[0,0,11,1], [0,0,0,1], [0,0,True,1], [0,0,1.5,1], [0,0,1]]:
            variants.append(dict(self.record, notes=[{"title": "x", "text": "y", "rect": rect}]))
        variants += [dict(self.record, image_sha256="wrong"), dict(self.record, page="../outside"),
                     dict(self.record, notes=[{"title": "", "text": "x"}])]
        for record in variants:
            with self.subTest(record=record):
                self.save(SOURCE, {"records": [record]})
                with self.assertRaises(ValueError):
                    apply_notes(self.root)
                self.assertEqual(self.outputs(), baseline)
        self.save(SOURCE, {"records": [self.record, self.record]})
        with self.assertRaises(ValueError):
            apply_notes(self.root)
        self.assertEqual(self.outputs(), baseline)


if __name__ == "__main__":
    unittest.main()
