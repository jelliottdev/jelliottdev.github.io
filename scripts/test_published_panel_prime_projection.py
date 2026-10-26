"""Independent archived panel projection bounds and mutation checks."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import published_panel_prime_projection as projection


class PanelProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(projection.known.runner, 'run', side_effect=AssertionError('Builder cannot execute a target')):
            cls.files = projection.prepare()
        cls.index = json.loads(cls.files[projection.INDEX_PATH])

    def mirror(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        plan = json.loads((projection.ROOT / projection.BASE / 'plan.json').read_bytes())
        names = {projection.BASE + '/' + name for name in projection.PINS}
        names.update(entry['path'] for entry in plan['inputs'])
        names.update(o['source'] for o in plan['openings'])
        names.update(['data/local-run-inputs.json', 'scripts/published_panel_prime_projection.py',
                      'scripts/published_known_key_projection.py', 'tools/research_runner.py', 'local-experiment.js'])
        for name in names:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(projection.ROOT / name, target)
        return root

    def changed_report(self, mutate):
        root = self.mirror()
        path = root / projection.BASE / 'results.json'
        report = json.loads(path.read_bytes())
        mutate(report)
        path.write_text(projection.stable(report), encoding='utf-8')
        pins = {**projection.PINS, 'results.json': projection.sha(path.read_bytes())}
        with patch.object(projection, 'PINS', pins):
            with self.assertRaises(ValueError):
                projection.audit(root)

    def test_original_independent_checker_passes(self):
        result = subprocess.run(['python', str(projection.ROOT / projection.BASE / 'check.py')], cwd=projection.ROOT, check=True, capture_output=True, text=True, timeout=30)
        self.assertIn('1760 inverse-checked outputs', result.stdout)
        self.assertIn('15,840 opening comparisons', result.stdout)

    def test_only_new_provider_paths_and_correct_explicit_empty_case_provenance(self):
        self.assertEqual(len(self.files), 35)
        self.assertEqual(len(self.index['entries']), 32)
        self.assertNotIn('data/published-program-source-index.json', self.files)
        self.assertNotIn('published-program-source-index-data.js', self.files)
        self.assertEqual(len({e['taskId'] for e in self.index['entries']}), 32)
        sidecar = json.loads(self.files[projection.AUDIT_PATH])
        self.assertEqual((sidecar['caseCount'], sidecar['comparisonCount'], sidecar['matchingCaseCount']), (1760, 15840, 0))
        self.assertEqual(sidecar['historicalRuneIndexCount'], 414592)
        self.assertEqual((sidecar['projectedCaseCount'], sidecar['structuralEmptyInputCaseCount']), (1792, 32))
        self.assertEqual(sidecar['emptyPages'], ['lp2-50'])
        self.assertEqual(sidecar['projectedCriterion'], 'warning')
        plan = json.loads((projection.ROOT / projection.BASE / 'plan.json').read_bytes())
        self.assertEqual(sidecar['openings'], plan['openings'])
        self.assertIn('not historical runs', sidecar['emptyInputMeaning'])
        self.assertNotIn('historicalDeclaredBeforeRun', sidecar)
        for e in self.index['entries']:
            raw = self.files[e['path']]
            self.assertEqual(e['bytes'], len(raw.encode('utf-8')))
            self.assertEqual(e['sha256'], projection.sha(raw))
            receipt = json.loads(raw)
            provenance = receipt['records'][0]['provenance']
            self.assertNotIn('followupId', provenance['projection'])
            self.assertEqual(provenance['projection']['ownerRecordId'], projection.RECORD)
            self.assertTrue(provenance['projection']['sourceProgramId'].startswith('panel-primes-'))
            self.assertEqual(e['revision'], projection.sha(projection.stable(provenance)))
            self.assertEqual(len(e['pages']), 56)
            source = receipt['entries'][0]
            self.assertEqual(source['run']['createdAt'], projection.CHECKED_AT)
            self.assertEqual(source['run']['id'], projection.sha(projection.stable(source['run']['result'])))
            empty = next(p for p in source['task']['pages'] if p['id'] == 'lp2-50')
            output = next(p for p in source['run']['result']['transformed'] if p['page'] == 'lp2-50')
            self.assertEqual(output['text'], empty['text'])
            self.assertFalse(next(m['matched'] for m in source['run']['result']['matches'] if m['page'] == 'lp2-50'))
            source_pins = {p['path']: p['sha256'] for p in provenance['sourcePins']}
            for name in ['scripts/published_panel_prime_projection.py', 'scripts/published_known_key_projection.py', 'tools/research_runner.py', 'local-experiment.js']:
                self.assertEqual(source_pins[name], projection.sha((projection.ROOT / name).read_bytes().replace(b'\r\n', b'\n')))

    def test_original_source_pins_and_current_bundle_cannot_change(self):
        for name in [projection.BASE + '/check.py', 'exports/fibonacci-prime-panel.json', 'text/lp2-50.txt']:
            with self.subTest(name=name):
                root = self.mirror()
                path = root / name
                path.write_bytes(path.read_bytes() + b' ')
                with self.assertRaisesRegex(ValueError, 'pin changed'):
                    projection.prepare(root)
        root = self.mirror()
        path = root / 'data/local-run-inputs.json'
        bundle = json.loads(path.read_bytes())
        next(p for p in bundle['pages'] if p['id'] == 'lp2-50')['raw'] += 'F'
        path.write_text(json.dumps(bundle), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Browser panel inputs differ'):
            projection.prepare(root)

    def test_inverse_array_integer_identity_and_all_nine_decisions_are_checked(self):
        changes = [lambda r: r['cases'][0]['output_indices'].__setitem__(0, (r['cases'][0]['output_indices'][0] + 1) % 29),
                   lambda r: r['cases'][0]['output_indices'].pop(),
                   lambda r: r['cases'][0]['output_indices'].__setitem__(0, True),
                   lambda r: r['cases'][0]['matching_openings'].append('warning'),
                   lambda r: r['cases'].append(copy.deepcopy(r['cases'][0])),
                   lambda r: r['cases'].__setitem__(0, {**r['cases'][0], 'offset': False}),
                   lambda r: r['cases'].pop(),
                   lambda r: r.__setitem__('empty_pages', []),
                   lambda r: r.__setitem__('comparison_count', 15841),
                   lambda r: r.__setitem__('distinct_page_outputs', 1759)]
        for mutate in changes:
            with self.subTest(change=changes.index(mutate)):
                self.changed_report(mutate)

    def test_current_runner_verifies_every_projected_receipt_separately_from_builder(self):
        receipts = [json.loads(self.files[e['path']])['entries'][0] for e in self.index['entries']]
        script = "const fs=require('fs'),E=require('./local-experiment.js'),{webcrypto}=require('crypto');(async()=>{const rows=JSON.parse(fs.readFileSync(0,'utf8'));let pages=0,runes=0,matched=0;for(const row of rows){await E.checkIdentity(row.task,webcrypto);const result=await E.verify(row.task,row.run.result,webcrypto);E.summary(row.task,result);pages+=result.metrics.pages;runes+=result.metrics.runes;matched+=result.matches.filter(m=>m.matched).length;}console.log(JSON.stringify({programs:rows.length,pages,runes,matched}));})().catch(e=>{console.error(e);process.exitCode=1;});"
        checked = subprocess.run(['node', '-e', script], cwd=projection.ROOT, input=json.dumps(receipts, ensure_ascii=False), text=True, capture_output=True, check=True, timeout=60, encoding='utf-8')
        self.assertEqual(json.loads(checked.stdout), {'programs': 32, 'pages': 1792, 'runes': 414592, 'matched': 0})

    def test_builder_write_and_check_are_idempotent_without_any_target_execution(self):
        root = self.mirror()
        with patch.object(projection.known.runner, 'run', side_effect=AssertionError('Builder cannot execute a target')):
            projection.build(root, write=True)
            before = {name: (root / name).read_bytes() for name in self.files}
            projection.build(root, write=True)
            projection.build(root, write=False)
        self.assertEqual(before, {name: (root / name).read_bytes() for name in self.files})
        path = root / self.index['entries'][0]['path']
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'Stale panel projection'):
            projection.build(root, write=False)


if __name__ == '__main__':
    unittest.main()
