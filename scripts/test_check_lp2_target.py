"""Known digest and exact-byte checks; no search for a target preimage."""
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
