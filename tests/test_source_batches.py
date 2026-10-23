"""Protect source scheduling against false blockers and dropped/duplicated work."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research'))
from prepare_source_batches import resolve, prepare
import cache_source_batches


class SourceBatchTests(unittest.TestCase):
    def test_link_fragment_and_unique_short_path(self):
        objects = {'liber-primus/analysis/I3/RESULTS.md': {'git_object': 'a'}}
        self.assertEqual(resolve('analysis/I3/RESULTS.md#control', objects)['status'], 'prefix-adjusted')
        self.assertEqual(resolve('RESULTS.md#control', objects)['status'], 'suffix-adjusted')
        objects['other/RESULTS.md'] = {'git_object': 'b'}
        self.assertEqual(resolve('RESULTS.md', objects)['status'], 'ambiguous')

    def test_shared_command_stays_together_and_reviewed_entries_stay_out(self):
        entries = [{'source_id': ident, 'source_hypothesis': ident,
                    'source_reproduction_command': command}
                   for ident, command in [('a', 'python same.py'), ('b', 'python same.py'), ('c', 'python other.py')]]
        entries.append({'source_id': 'done', 'reviewed_subclaims': {}})
        result = prepare({'entries': entries}, {}, batch_count=2)
        self.assertEqual(result['pending_entry_count'], 3)
        groups = [group['source_ids'] for batch in result['batches'] for group in batch['groups']]
        self.assertIn(['a', 'b'], groups)
        self.assertEqual(sorted(x for group in groups for x in group), ['a', 'b', 'c'])

    def test_register_covers_snapshot_exactly_and_receipts_match(self):
        pack = json.loads((ROOT / 'research/source-batches-2026-10-23.json').read_bytes())
        audit = json.loads((ROOT / 'research/source-audit-register.json').read_bytes())
        expected = [e['source_id'] for b in pack['batches'] for g in b['groups'] for e in g['entries']]
        actual = [row['source_id'] for row in audit['entries']]
        self.assertEqual(len(actual), len(set(actual)))
        self.assertEqual(set(actual), set(expected))
        self.assertTrue(all(row['independently_replayed_by_audit'] is False for row in audit['entries']))
        for receipt in audit['receipts']:
            raw = (ROOT / receipt['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), receipt['sha256'])
            self.assertNotIn(chr(65533), raw.decode('utf-8'))

    def test_valid_cache_avoids_git_fetch_and_corruption_is_repaired(self):
        raw = b'original source bytes\n'
        oid = cache_source_batches.object_id(raw)
        objects = {'analysis/a.py': {'git_object': oid, 'mode': '100644',
                                    'bytes': len(raw), 'kind': 'blob'}}
        pack = {'revision': cache_source_batches.REVISION, 'batches': [{'groups': [
            {'entries': [{'evidence': [{'candidates': [{'path': 'analysis/a.py'}]}]}]}]}]}
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            target = cache / (oid + '.txt')
            target.write_bytes(raw)
            with patch.object(cache_source_batches, 'tree', return_value=objects), \
                 patch.object(cache_source_batches.subprocess, 'check_output') as fetch:
                result = cache_source_batches.cache_sources(Path('unused'), pack, cache)
                self.assertEqual(result['reused'], 1)
                fetch.assert_not_called()
                target.write_bytes(b'corrupted')
                fetch.return_value = f'{oid} blob {len(raw)}\n'.encode() + raw + b'\n'
                result = cache_source_batches.cache_sources(Path('unused'), pack, cache)
                self.assertEqual(result['fetched'], 1)
                self.assertEqual(target.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
