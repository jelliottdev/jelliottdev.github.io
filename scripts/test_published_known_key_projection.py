"""Independent bounds and mutation checks for the archived known-key importer."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import published_known_key_projection as projection


class ProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = projection.prepare()
        cls.index = json.loads(cls.files['data/published-program-source-index.json'])

    def mirror(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        plan = json.loads((projection.ROOT / projection.BASE / 'plan.json').read_bytes())
        report = json.loads((projection.ROOT / projection.BASE / 'results.json').read_bytes())
        paths = {projection.BASE + '/' + n for n in projection.PINS}
        paths.update(r['path'] for r in report['inputs'])
        paths.update(r['source'] for r in plan['openings'])
        paths.update(['data/index.json', 'data/local-run-inputs.json'])
        for name in paths:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(projection.ROOT / name, target)
        return root

    def mutate_report(self, change):
        root = self.mirror()
        path = root / projection.BASE / 'results.json'
        value = json.loads(path.read_bytes())
        change(value)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        pins = dict(projection.PINS, **{'results.json': projection.sha(path.read_bytes())})
        return root, pins

    def test_complete_bounded_receipts_and_original_evaluations(self):
        self.assertEqual(len(self.index['entries']), 42)
        self.assertEqual(len({r['taskId'] for r in self.index['entries']}), 42)
        for entry in self.index['entries']:
            content = self.files[entry['path']]
            self.assertEqual(entry['bytes'], len(content.encode('utf-8')))
            self.assertEqual(entry['sha256'], projection.sha(content))
            self.assertLess(entry['bytes'], 200000)
            receipt = json.loads(content)
            record, result = receipt['records'][0], receipt['entries'][0]['run']['result']
            self.assertEqual(record['provenance']['projection']['sourceProgramId'], entry['caseId'].removesuffix('--all-pages'))
            self.assertNotIn('followupId', record['provenance']['projection'])
            self.assertEqual(record['revision'], projection.sha(projection.stable(record['provenance'])))
            self.assertEqual(entry['resultId'], projection.sha(projection.stable(result)))
            self.assertEqual(result['metrics']['pages'], 56)
            self.assertEqual(result['metrics']['runes'], 12956)
            self.assertEqual(result['matches'], [{'page': f'lp2-{n:02d}', 'matched': False} for n in range(56)])
            task = receipt['entries'][0]['task']
            self.assertEqual(result['transformed'][50]['text'], task['pages'][50]['text'])
            self.assertEqual(entry['criterion']['values'], [24,7,24,4,9,21,17,18,20,10,18,1])
            self.assertIn('not a historical browser submission', record['provenance']['dateMeaning'])
        audit = json.loads(self.files[projection.AUDIT_PATH])
        self.assertEqual((len(audit['openings']), audit['caseCount'], audit['comparisonCount'], audit['matchingCaseCount']), (9,2352,21168,0))

    def test_no_target_execution_and_deterministic_bytes(self):
        with patch.object(projection.runner, 'run', side_effect=AssertionError('Target execution forbidden')), patch.object(projection.runner, 'transform', side_effect=AssertionError('Target execution forbidden')):
            self.assertEqual(projection.prepare(), self.files)

    def test_source_pin_mutation_fails_closed(self):
        root = self.mirror()
        with (root / projection.BASE / 'run.py').open('ab') as stream:
            stream.write(b'\n# changed\n')
        with self.assertRaisesRegex(ValueError, 'source pin'):
            projection.audit(root)

    def test_output_mutation_rejected_even_with_rebound_report_pin(self):
        root, pins = self.mutate_report(lambda r: r['cases'][0]['output_indices'].__setitem__(0, (r['cases'][0]['output_indices'][0] + 1) % 29))
        with patch.object(projection, 'PINS', pins), self.assertRaisesRegex(ValueError, 'key equation'):
            projection.audit(root)

    def test_missing_duplicate_and_truncated_cases_rejected(self):
        mutations = [lambda r: r['cases'].pop(), lambda r: r['cases'].append(copy.deepcopy(r['cases'][0])), lambda r: r['cases'][0]['output_indices'].pop()]
        for change in mutations:
            root, pins = self.mutate_report(change)
            with patch.object(projection, 'PINS', pins), self.assertRaises(ValueError):
                projection.audit(root)

    def test_opening_decisions_and_input_drift_rejected(self):
        root, pins = self.mutate_report(lambda r: r['cases'][0]['matching_openings'].append('warning'))
        with patch.object(projection, 'PINS', pins), self.assertRaisesRegex(ValueError, 'evaluations'):
            projection.audit(root)
        root = self.mirror()
        with (root / 'text/lp2-00.txt').open('ab') as stream:
            stream.write(b' ')
        with self.assertRaisesRegex(ValueError, 'input pin'):
            projection.audit(root)


if __name__ == '__main__':
    unittest.main()
