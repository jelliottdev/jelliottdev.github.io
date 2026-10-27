"""Exercise the publication check with actual Git-normalized and preserved bytes."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from check_staged_catalog import verify


class StagedCatalogTests(unittest.TestCase):
    def fixture(self, root, preserve):
        subprocess.run(['git', 'init', '-q', str(root)], check=True)
        subprocess.run(['git', 'config', 'core.autocrlf', 'false'], cwd=root, check=True)
        (root / 'data').mkdir()
        raw = b'{"value": 1}\r\n'
        (root / 'rows.jsonl').write_bytes(raw)
        (root / '.gitattributes').write_text(
            'rows.jsonl -text\n' if preserve else 'rows.jsonl text eol=lf\n', encoding='utf-8')
        (root / 'data/catalog.json').write_text(json.dumps({'files': [{
            'path': 'rows.jsonl', 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()
        }]}), encoding='utf-8')
        subprocess.run(['git', 'add', '.'], cwd=root, check=True, capture_output=True)

    def test_detects_line_ending_change_even_when_working_file_matches(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root, preserve=False)
            with self.assertRaisesRegex(AssertionError, 'Staged size differs: rows.jsonl'):
                verify(root, all_files=True)

    def test_preserved_input_matches_in_changed_and_full_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root, preserve=True)
            self.assertEqual(verify(root), 1)
            self.assertEqual(verify(root, all_files=True), 1)

    def test_local_retained_snapshot_must_exist_in_git_index_before_publication(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root, preserve=True)
            raw = b'{"id":"historical-record","status":"published"}\n'
            digest = hashlib.sha256(raw).hexdigest()
            name = 'published-sources/records/' + digest + '.json'
            snapshot = root / name
            snapshot.parent.mkdir(parents=True)
            snapshot.write_bytes(raw)
            catalog = json.loads((root / 'data/catalog.json').read_text(encoding='utf-8'))
            catalog['files'].append({'path': name, 'bytes': len(raw), 'sha256': digest})
            (root / 'data/catalog.json').write_text(json.dumps(catalog), encoding='utf-8')
            # A generated catalog and valid local object are insufficient: only
            # indexed bytes will be present in the published checkout.
            subprocess.run(['git', 'add', 'data/catalog.json'], cwd=root, check=True)
            self.assertEqual(snapshot.read_bytes(), raw)
            self.assertEqual(subprocess.check_output(['git', 'ls-files', '--', name], cwd=root), b'')
            with self.assertRaisesRegex(AssertionError, 'Missing staged file: ' + name):
                verify(root, all_files=True)
            subprocess.run(['git', 'add', '--', name], cwd=root, check=True)
            self.assertEqual(verify(root, all_files=True), 2)
            self.assertEqual(snapshot.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
