"""Known digest and exact-byte checks; no search for a target preimage."""
import tempfile
import unittest
import json
import shutil
import subprocess
import sys
from pathlib import Path
from check_lp2_target import compare_file, target_record

ABC_SHA512 = (
    "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a"
    "2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f"
)


class CandidateChecks(unittest.TestCase):
    def test_known_digest_and_literal_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "candidate"
            path.write_bytes(b"abc")
            result = compare_file(path, ABC_SHA512, "fixture")
            self.assertTrue(result["matches"])
            self.assertEqual(result["candidate_bytes"], 3)
            self.assertEqual(path.read_bytes(), b"abc")
            path.write_bytes(b"abc\n")
            self.assertFalse(compare_file(path, ABC_SHA512, "fixture")["matches"])
            path.write_bytes(b"abc\r\n")
            self.assertFalse(compare_file(path, ABC_SHA512, "fixture")["matches"])

    def test_real_target_is_not_fixture(self):
        target, record_hash = target_record()
        self.assertEqual(len(target), 128)
        self.assertEqual(len(record_hash), 64)
        self.assertNotEqual(target, ABC_SHA512)

    def test_missing_file_is_an_error(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError):
                compare_file(Path(folder) / "missing", ABC_SHA512, "fixture")

    def test_invalid_target_structure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "data/pages/lp2-56.json"
            path.parent.mkdir(parents=True)
            for value in [
                None, [], {"id": "lp2-55"},
                {"id": "lp2-56", "reading": None},
                {"id": "lp2-56", "reading": {"literal": 123}},
                {"id": "lp2-56", "reading": {"literal": "not a digest"}},
            ]:
                with self.subTest(value=value):
                    path.write_text(json.dumps(value), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        target_record(root)

    def test_invalid_target_cli_status(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "scripts").mkdir()
            script = root / "scripts/check_lp2_target.py"
            shutil.copyfile(Path(__file__).with_name("check_lp2_target.py"), script)
            target = root / "data/pages/lp2-56.json"
            target.parent.mkdir(parents=True)
            target.write_text("null", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(script), "unused-candidate"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertIn("Target record must identify page lp2-56", result.stderr)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
