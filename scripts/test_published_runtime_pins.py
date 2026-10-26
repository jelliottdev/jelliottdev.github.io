"""Historical import bytes stay immutable across runtime upgrades; no target execution."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import published_known_key_projection as projection

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'scripts/published_known_key_projection.py': '824029e9b72d0eeaf84890ad5f966c101472c47d5ff47e9d0cf7f0eba1b95aea',
    'tools/research_runner.py': 'be73adac90d9b7cf7ee8a7b2f11bdd1d7a61974e84b21a5566ca97f37a1d0c61',
    'local-experiment.js': 'b2f38df4184a36f1462cfea120c1d121dde05babdb29e30f97442d8528b762c2',
}

class HistoricalRuntimeRetention(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = {p: p.read_bytes() for p in (ROOT / 'published-evidence/programs').glob('known-keys-*.json')}
        cls.before.update({ROOT / name: (ROOT / name).read_bytes() for name in ('data/published-program-source-index.json', 'published-program-source-index-data.js', projection.AUDIT_PATH)})
        with patch.object(projection.runner, 'run', side_effect=AssertionError('No target execution')):
            cls.generated = projection.prepare(ROOT)

    def temporary_sources(self, root):
        receipt = json.loads(next(iter(self.before.values())))
        sources = {pin['path'] for pin in receipt['records'][0]['provenance']['sourcePins']}
        sources.discard(projection.AUDIT_PATH)
        sources.update(('data/index.json', 'data/local-run-inputs.json'))
        for source in sources:
            target = root / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / source, target)
        for source, digest in EXPECTED.items():
            relative = 'published-sources/runtime/' + digest + Path(source).suffix
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def test_unchanged_all_42_receipts_indexes_and_audit(self):
        self.assertEqual(len(self.before), 45)
        self.assertEqual(projection.HISTORICAL_CODE_PINS, EXPECTED)
        for source, digest in EXPECTED.items():
            retained = ROOT / 'published-sources/runtime' / (digest + Path(source).suffix)
            self.assertEqual(hashlib.sha256(retained.read_bytes()).hexdigest(), digest)
        for name, generated in self.generated.items():
            self.assertEqual(generated.encode('utf-8'), self.before[ROOT / name], name)
        self.assertEqual({p: p.read_bytes() for p in self.before}, self.before)

    def test_current_runtime_edits_leave_every_generated_historical_byte_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.temporary_sources(root)
            for source in EXPECTED:
                (root / source).write_text('Changed current runtime; never executed.\n', encoding='utf-8')
            with patch.object(projection.runner, 'run', side_effect=AssertionError('No target execution')):
                self.assertEqual(projection.prepare(root), self.generated)
        self.assertEqual({p: p.read_bytes() for p in self.before}, self.before)

    def test_each_missing_corrupt_or_newline_changed_retained_body_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.temporary_sources(root)
            for source, digest in EXPECTED.items():
                retained = root / 'published-sources/runtime' / (digest + Path(source).suffix)
                original = retained.read_bytes()
                retained.unlink()
                with self.assertRaisesRegex(ValueError, 'Historical projection code'):
                    projection.historical_code_pins(root)
                for corrupted in (b'Changed retained code', original.replace(b'\n', b'\r\n')):
                    retained.write_bytes(corrupted)
                    with self.assertRaisesRegex(ValueError, 'Historical projection code'):
                        projection.historical_code_pins(root)
                retained.write_bytes(original)
            self.assertEqual(projection.historical_code_pins(root), EXPECTED)

if __name__ == '__main__':
    unittest.main()
