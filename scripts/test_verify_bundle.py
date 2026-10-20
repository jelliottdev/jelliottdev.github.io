import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from verify_bundle import verify


class VerifyBundle(unittest.TestCase):
    def test_correct_changed_and_missing_members(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = b"A\n"
            member = root / "example.txt"
            member.write_bytes(data)
            manifest = root / "CONTENTS.json"
            manifest.write_text(json.dumps([dict(path="example.txt", bytes=len(data),
                                                 sha256=hashlib.sha256(data).hexdigest())]))
            self.assertEqual(verify(manifest), (1, []))
            member.write_bytes(b"B\n")  # Same size is insufficient.
            self.assertEqual(verify(manifest)[0], 0)
            self.assertIn("mismatch", verify(manifest)[1][0])
            member.unlink()
            self.assertIn("missing", verify(manifest)[1][0])

    def test_manifest_paths_and_duplicates(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = Path(folder) / "CONTENTS.json"
            for name in ["../outside.txt", "/outside.txt", "C:/outside.txt", "a\\b"]:
                manifest.write_text(json.dumps([dict(path=name, bytes=0, sha256="0"*64)]))
                with self.assertRaises(ValueError):
                    verify(manifest)
            row = dict(path="file.txt", bytes=0, sha256="0"*64)
            manifest.write_text(json.dumps([row, row]))
            with self.assertRaises(ValueError):
                verify(manifest)


if __name__ == "__main__":
    unittest.main()
