"""Check provenance in the structural report, without requiring image packages."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
import tempfile
import shutil
import importlib.util


class VisualReport(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow is optional")
    def test_wrong_image_rejected_before_decoding_with_optimization(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            for directory in ("scripts", "data/pages", "images"):
                (target / directory).mkdir(parents=True)
            shutil.copyfile(root / "scripts/inspect_visual_records.py",
                            target / "scripts/inspect_visual_records.py")
            shutil.copyfile(root / "data/pages/lp2-00.json", target / "data/pages/lp2-00.json")
            (target / "images/lp2-00.jpg").write_bytes(b"deliberately incorrect image")
            for flags in ([], ["-O"]):
                result = subprocess.run(
                    [sys.executable, *flags, str(target / "scripts/inspect_visual_records.py"), "--pixels"],
                    capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn("original image SHA-256 mismatch", result.stderr)

    def test_invalid_inventory_rejected_even_with_optimization(self):
        root = Path(__file__).resolve().parents[1]
        changes = [
            ("glyph ordinals", lambda page: page["visual"]["glyphs"][0].update(ordinal=999)),
            ("positive size", lambda page: page["visual"]["glyphs"][0].update(rectangle=[0, 0, 0, 1])),
            ("image bounds", lambda page: page["visual"]["glyphs"][0].update(rectangle=[0, 0, 99999, 1])),
            ("must be integers", lambda page: page["visual"]["glyphs"][0].update(rectangle=[0.5, 0, 1, 1])),
        ]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            (target / "scripts").mkdir()
            (target / "data/pages").mkdir(parents=True)
            shutil.copyfile(root / "scripts/inspect_visual_records.py",
                            target / "scripts/inspect_visual_records.py")
            for pid in ("lp2-00", "lp2-01", "lp2-02"):
                shutil.copyfile(root / f"data/pages/{pid}.json", target / f"data/pages/{pid}.json")
            original = (root / "data/pages/lp2-00.json").read_bytes()
            for expected, change in changes:
                page = json.loads(original)
                change(page)
                (target / "data/pages/lp2-00.json").write_text(json.dumps(page), encoding="utf-8")
                for flags in ([], ["-O"]):
                    with self.subTest(change=expected, flags=flags):
                        result = subprocess.run(
                            [sys.executable, *flags, str(target / "scripts/inspect_visual_records.py")],
                            capture_output=True, text=True)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertEqual(result.stdout, "")
                        self.assertIn(expected, result.stderr)

    def test_structural_report_does_not_claim_image_verification(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, str(root / "scripts/inspect_visual_records.py")],
            capture_output=True, check=True,
        )
        report = json.loads(result.stdout)
        self.assertFalse(report["pixel_recount"])
        self.assertIsNone(report["pillow_version"])
        self.assertEqual([row["page"] for row in report["pages"]],
                         ["lp2-00", "lp2-01", "lp2-02"])
        for row in report["pages"]:
            record = (root / row["record_path"]).read_bytes()
            self.assertEqual(row["record_sha256"], hashlib.sha256(record).hexdigest())
            self.assertEqual(row["expected_image_sha256"], json.loads(record)["image_sha256"])
            self.assertFalse(row["image_hash_verified"])
            self.assertEqual(sum(row["punctuation_component_counts"].values()),
                             row["punctuation_regions"])


if __name__ == "__main__":
    unittest.main()
