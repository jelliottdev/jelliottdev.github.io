"""Detached source-array receipt proof, never an installed evidence provider."""
import copy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import numeric_bank_followups as numeric
import published_numeric_bank_projection as projection


class NumericProjectionProof(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = {path: path.read_bytes() for rid in numeric.FAMILIES for path in (numeric.ROOT / 'experiments/records' / rid).glob('*') if path.is_file()}
        with patch.object(numeric.fixed.runner, 'run', side_effect=AssertionError('Projection must not execute targets')):
            cls.prepared = {rid: projection.prepare(rid) for rid in numeric.FAMILIES}
            cls.receipts = {rid: [value.receipt(program['id']) for program in value.manifest()['payload']['programs']] for rid, value in cls.prepared.items()}

    def test_all_sources_preserved_58_programs_and_complete_original_criteria(self):
        self.assertEqual({path: path.read_bytes() for path in self.before}, self.before)
        for rid, prepared in self.prepared.items():
            manifest = prepared.manifest()
            payload = manifest['payload']
            self.assertEqual(manifest['sha256'], projection.digest(payload))
            self.assertEqual(payload['declaredCases'], 3248)
            self.assertEqual(payload['structuralEmptyCases'], 58)
            self.assertEqual(payload['audit']['historicalCases'], 3190)
            self.assertEqual(payload['audit']['historicalComparisons'], 28710)
            self.assertEqual(len(payload['programs']), 58)
            self.assertEqual(len({p['id'] for p in payload['programs']}), 58)
            self.assertEqual(len({projection.stable(row) for row in payload['outputs']}), len(payload['outputs']))
            self.assertEqual({(p['offset'], p['direction']) for p in payload['programs']}, {(n, direction) for n in range(29) for direction in ['subtract', 'add']})
            self.assertEqual(payload['criterion']['kind'], 'exact-prefix-set')
            self.assertEqual(len(payload['criterion']['openings']), 9)
            for receipt in self.receipts[rid]:
                provenance = receipt['records'][0]['provenance']
                row = receipt['entries'][0]
                self.assertEqual(row['task']['criterion'], payload['criterion'])
                self.assertEqual(row['revision'], projection.digest(provenance))
                self.assertEqual(row['task']['taskId'], projection.fixed.runner.task_identity(row['task']))
                self.assertEqual(row['run']['id'], projection.digest(row['run']['result']))
                self.assertEqual(row['run']['createdAt'], projection.CHECKED_AT)
                self.assertIn('no historical browser execution date', provenance['dateMeaning'])
                self.assertIn('not a historical run', provenance['verificationMeaning'])
                self.assertFalse(any(m['matched'] for m in row['run']['result']['matches']))
                empty = next(m for m in row['run']['result']['matches'] if m['page'] == 'lp2-50')
                self.assertEqual(empty, {'page': 'lp2-50', 'matched': False, 'matchingOpenings': []})

    def test_deduplicated_fibonacci_aliases_preserve_all_named_programs_and_exact_tail_lengths(self):
        for rid, prepared in self.prepared.items():
            payload = prepared.manifest()['payload']
            family = numeric.FAMILIES[rid]
            self.assertLess(len(payload['outputs']), 3248)
            self.assertEqual(len([row for row in payload['outputs'] if row['origin'] == 'structural-empty-input']), 1)
            if rid == 'lp2-fibonacci-openings':
                self.assertLess(len(payload['outputs']), 3190)
                first = next(p for p in payload['programs'] if p['offset'] == 0 and p['direction'] == 'add')
                alias = next(p for p in payload['programs'] if p['offset'] == 14 and p['direction'] == 'add')
                self.assertEqual(first['outputRefs'], alias['outputRefs'])
                self.assertNotEqual(prepared.receipt(first['id'])['entries'][0]['task']['taskId'], prepared.receipt(alias['id'])['entries'][0]['task']['taskId'])
            for receipt in self.receipts[rid]:
                task = receipt['entries'][0]['task']
                offset = next(p['offset'] for p in payload['programs'] if p['id'] == receipt['records'][0]['provenance']['projection']['id'])
                self.assertEqual(task['steps'][0]['key'], numeric.banks.resolve(family['bankId'], family['bankSha256'], offset))
                self.assertEqual(len(task['steps'][0]['key']), 305-offset)

    def test_detached_views_and_immutable_bytes_cannot_rewrite_prepared_receipts(self):
        prepared = self.prepared['lp2-prime-openings']
        first = prepared.manifest()['payload']['programs'][0]['id']
        before = prepared.receipt(first)
        view = prepared.manifest()
        view['payload']['outputs'][0]['values'][0] = 99
        self.assertEqual(prepared.receipt(first), before)
        with self.assertRaises(FrozenInstanceError):
            prepared._bytes = b'changed'
        with self.assertRaisesRegex(ValueError, 'Unknown or ambiguous'):
            prepared.receipt('unowned-program')

    def test_source_changes_duplicate_rows_and_bank_tail_drift_are_rejected(self):
        rid = 'lp2-prime-openings'
        with patch.object(numeric, 'source', side_effect=ValueError('changed source pin')), self.assertRaisesRegex(ValueError, 'source pin'):
            projection.prepare(rid)
        prepared = self.prepared[rid]
        program = prepared.manifest()['payload']['programs'][0]
        task = prepared.receipt(program['id'])['entries'][0]['task']
        rows = [copy.deepcopy(prepared.manifest()['payload']['outputs'][n]) for n in program['outputRefs']]
        for change in [lambda r: r[0]['values'].__setitem__(0, (r[0]['values'][0]+1)%29), lambda r: r[0]['values'].pop(), lambda r: r[0]['matchingOpenings'].append('warning'), lambda r: r[0].__setitem__('origin', 'structural-empty-input')]:
            bad = copy.deepcopy(rows)
            change(bad)
            with self.assertRaises(ValueError):
                projection.format_result(task, bad)
        bad_task = copy.deepcopy(task)
        bad_task['steps'][0]['key'][0] = (bad_task['steps'][0]['key'][0]+1)%29
        with self.assertRaisesRegex(ValueError, 'inverse arithmetic'):
            projection.format_result(bad_task, rows)
        tail = numeric.banks.resolve(numeric.FAMILIES[rid]['bankId'], numeric.FAMILIES[rid]['bankSha256'], 0)
        tail[-1] = (tail[-1]+1)%29
        with patch.object(numeric.banks, 'resolve', return_value=tail), self.assertRaisesRegex(ValueError, 'bank tail changed'):
            prepared.receipt(program['id'])
        with self.assertRaisesRegex(ValueError, 'page scope'):
            projection.format_result(task, rows[:-1])
        manifest = prepared.manifest()
        manifest['payload']['programs'].append(copy.deepcopy(program))
        manifest['sha256'] = projection.digest(manifest['payload'])
        with self.assertRaisesRegex(ValueError, 'Unknown or ambiguous'):
            projection.Projection(manifest).receipt(program['id'])
        path = numeric.ROOT / 'experiments/records' / rid / 'results.json'
        raw = path.read_bytes();report = json.loads(raw);report['cases'].append(copy.deepcopy(report['cases'][0]));changed=json.dumps(report).encode()
        families = copy.deepcopy(numeric.FAMILIES)
        families[rid]['pins']['results.json'] = numeric.digest(changed)
        with patch.object(numeric, 'FAMILIES', families), patch.object(Path, 'read_bytes', lambda p: changed if p == path else self.before[p] if p in self.before else original(p)), self.assertRaisesRegex(ValueError, 'duplicated'):
            projection.prepare(rid)

    def test_detached_publication_files_bind_232_headers_to_four_shared_sources(self):
        class Cached:
            def __init__(self, prepared, receipts):
                self.prepared = prepared
                self.receipts = {r['records'][0]['provenance']['projection']['id']: r for r in receipts}
            def bytes(self): return self.prepared.bytes()
            def manifest(self): return self.prepared.manifest()
            def receipt(self, program_id): return copy.deepcopy(self.receipts[program_id])
        cache = {rid: Cached(value, self.receipts[rid]) for rid, value in self.prepared.items()}
        with patch.object(projection, 'prepare', side_effect=lambda rid, root: cache[rid]), patch.object(numeric.fixed.runner, 'run', side_effect=AssertionError('No target computation')):
            files = projection.publication_files()
        self.assertEqual(len(files), 5)
        index = json.loads(files['data/published-numeric-program-source-index.json'])
        self.assertEqual(len(index['entries']), 232)
        seen = set()
        for pointer in index['entries']:
            self.assertEqual(pointer['sourceFormat'], 'numeric-bank-matrix-v1')
            raw = files[pointer['path']]
            self.assertEqual(pointer['bytes'], len(raw))
            self.assertEqual(pointer['sha256'], numeric.digest(raw))
            receipt = cache[pointer['recordId']].receipt(pointer['programId'])
            row = receipt['entries'][0]
            self.assertEqual(pointer['taskId'], row['task']['taskId'])
            self.assertEqual(pointer['resultId'], row['run']['id'])
            self.assertEqual(pointer['revision'], row['revision'])
            self.assertEqual(pointer['steps'], row['task']['steps'])
            self.assertEqual(pointer['criterion'], row['task']['criterion'])
            self.assertNotIn(pointer['programId'], seen)
            seen.add(pointer['programId'])
        self.assertEqual(len({p['path'] for p in index['entries']}), 4)
        self.assertEqual({path: path.read_bytes() for path in self.before}, self.before)

    def test_all_232_complete_current_engine_receipts_verify_separately_from_projection(self):
        script = r"""const E=require('./local-experiment.js'),fs=require('node:fs'),crypto=require('node:crypto');(async()=>{const sources=JSON.parse(fs.readFileSync(0,'utf8'));let pages=0,runes=0,matches=0;for(const receipt of sources){const row=receipt.entries[0];await E.checkIdentity(row.task,crypto.webcrypto);const result=await E.verify(row.task,row.run.result,crypto.webcrypto);E.summary(row.task,result);pages+=result.metrics.pages;runes+=result.metrics.runes;matches+=result.matches.filter(m=>m.matched).length;}console.log(JSON.stringify({programs:sources.length,pages,runes,matches}));})().catch(e=>{console.error(e);process.exitCode=1;});"""
        for rid, receipts in self.receipts.items():
            checked = subprocess.run(['node', '-e', script], cwd=numeric.ROOT, input=json.dumps(receipts, ensure_ascii=False), text=True, capture_output=True, encoding='utf8', check=True, timeout=90)
            self.assertEqual(json.loads(checked.stdout), {'programs': 58, 'pages': 3248, 'runes': 751448, 'matches': 0})


original = Path.read_bytes
if __name__ == '__main__':
    unittest.main()
