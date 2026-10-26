"""Repacking preserves scientific bytes and both exact source revisions."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import archive_authored_sources as archive
import finite_control_storage as storage
import repack_finite_controls as repack


class RepackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = json.loads((repack.ROOT / 'experiments/records/public-wordlist-vigenere/record.json').read_bytes())
        self.record = {'id': 'fixture', 'status': 'published', 'finding': 'Scientific finding stays exact.',
                       'browser_followups': [copy.deepcopy(source['browser_followups'][0])]}
        self.followup = self.record['browser_followups'][0]['id']
        self.path = self.root / 'experiments/records/fixture/record.json'
        self.path.parent.mkdir(parents=True)
        self.raw = (json.dumps(self.record, ensure_ascii=False, indent=1) + '\r\n').encode('utf-8')
        self.path.write_bytes(self.raw)

    def test_preview_is_read_only_and_exact_expanded_content_is_identical(self):
        report = repack.repack(self.root, 'fixture', self.followup)
        self.assertFalse(report['written'])
        self.assertEqual(report['targetExecutions'], 0)
        self.assertLess(report['afterBytes'], report['beforeBytes'])
        self.assertEqual(self.path.read_bytes(), self.raw)
        self.assertFalse((self.root / archive.MANIFEST).exists())

    def test_write_retains_both_exact_revisions_and_is_idempotent(self):
        report = repack.repack(self.root, 'fixture', self.followup, write=True)
        self.assertTrue(report['written'])
        updated_raw = self.path.read_bytes()
        updated = json.loads(updated_raw)
        self.assertEqual(updated['finding'], self.record['finding'])
        old = copy.deepcopy(self.record)
        old['browser_followups'][0]['control'] = storage.expand(old['browser_followups'][0]['control'])
        restored = copy.deepcopy(updated)
        restored['browser_followups'][0]['control'] = storage.expand(restored['browser_followups'][0]['control'])
        self.assertEqual(restored, old)
        entries = archive.build(self.root)['entries']
        self.assertEqual(len(entries), 2)
        retained = {(self.root / item['path']).read_bytes() for item in entries}
        self.assertEqual(retained, {self.raw, updated_raw})
        again = repack.repack(self.root, 'fixture', self.followup, write=True)
        self.assertFalse(again['changed'])
        self.assertEqual(self.path.read_bytes(), updated_raw)
        self.assertEqual(len(archive.build(self.root)['entries']), 2)

    def test_unknown_or_escaping_selection_never_writes(self):
        for record_id, followup in [('../fixture', self.followup), ('fixture', '../other'), ('fixture', 'missing')]:
            with self.subTest(record_id=record_id, followup=followup), self.assertRaises(ValueError):
                repack.repack(self.root, record_id, followup, write=True)
        self.assertEqual(self.path.read_bytes(), self.raw)
        self.assertFalse((self.root / archive.MANIFEST).exists())

    def test_changed_controls_and_concurrent_source_edits_are_not_overwritten(self):
        packed = storage.compact_pooled(self.record['browser_followups'][0]['control'])
        packed['rows'][0][7] = '0' * 64
        with patch.object(storage, 'compact_pooled', return_value=packed), self.assertRaisesRegex(ValueError, 'changed the expanded'):
            repack.repack(self.root, 'fixture', self.followup, write=True)
        self.assertEqual(self.path.read_bytes(), self.raw)
        other = self.raw + b' '
        with patch.object(archive, 'build', side_effect=lambda *a, **kw: self.path.write_bytes(other)), self.assertRaisesRegex(ValueError, 'source changed'):
            repack.repack(self.root, 'fixture', self.followup, write=True)
        self.assertEqual(self.path.read_bytes(), other)


if __name__ == '__main__':
    unittest.main()
