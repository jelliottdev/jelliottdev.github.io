"""Check provenance in the structural report, without requiring image packages."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest


class VisualReport(unittest.TestCase):
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
