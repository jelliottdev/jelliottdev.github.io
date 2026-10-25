"""Exact historical exclusions become explicit fresh fixed-program receipts."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from published_program_projection import ROOT, BASE, DECLARATION, source_files, build, sha, stable, independent_row_atbash


class ProgramProjectionTests(unittest.TestCase):
    def fixture(self):
        directory = tempfile.TemporaryDirectory(prefix='liberpedia-program-projection-test-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        names = source_files() + ['data/local-run-inputs.json', 'local-experiment.js', 'scripts/published_program_projection.py', 'data/published-opening-evidence.json', 'published-opening-evidence-data.js']
        for name in names:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        return root

    def test_complete_55_page_projection_has_exact_source_program_receipt_and_explicit_fresh_date(self):
        manifest = build(write=False)
        self.assertEqual(manifest['schema'], 'liberpedia-published-program-evidence-v1')
        record, entry = manifest['records'][0], manifest['entries'][0]
        self.assertEqual(len(manifest['entries']), 1)
        self.assertEqual(entry['recordId'], 'prepared-opening-evidence-gates')
        self.assertEqual(entry['caseId'], 'row-reversal-atbash-warning--all-pages')
        self.assertEqual(len(entry['task']['pages']), 55)
        self.assertNotIn('lp2-50', [p['id'] for p in entry['task']['pages']])
        self.assertEqual(entry['task']['steps'], DECLARATION['steps'])
        self.assertEqual(entry['task']['criterion'], DECLARATION['criterion'])
        self.assertTrue(all(row['matched'] is False for row in entry['run']['result']['matches']))
        provenance = record['provenance']
        self.assertEqual(sha(stable(provenance)), record['revision'])
        self.assertEqual(sha(stable(entry['run']['result'])), entry['run']['id'])
        self.assertEqual(provenance['projection']['taskId'], entry['task']['taskId'])
        self.assertEqual(provenance['projection']['resultId'], entry['run']['id'])
        self.assertEqual(provenance['projection']['steps'], entry['task']['steps'])
        self.assertEqual(provenance['projection']['ownerRecordId'], 'lp2-row-column-routes')
        pins = {p['path']: p['sha256'] for p in provenance['sourcePins']}
        self.assertEqual(len(pins), 72)
        self.assertTrue(set(DECLARATION['sourceSha256']) <= set(pins))
        self.assertIn('not a historical browser submission', provenance['dateMeaning'])
        self.assertIn('did not contain these full transformed outputs', provenance['verificationMeaning'])
        self.assertEqual(entry['run']['createdAt'], provenance['checkedAt'])
        code = "const D=require('./published-opening-evidence-data.js'),E=require('./local-experiment.js');(async()=>{const e=D.entries[0];if(!Object.isFrozen(e.run.result.transformed))throw Error('Mutable');await E.verify(e.task,e.run.result);})().catch(e=>{console.error(e);process.exitCode=1;});"
        subprocess.run(['node', '-e', code], cwd=ROOT, check=True, capture_output=True)

    def test_independent_ordering_control_preserves_separators_and_handles_both_newline_bytes(self):
        alphabet = [{'rune': chr(65 + n)} for n in range(29)]
        value = independent_row_atbash('AB-C\r\nD E\nF', alphabet)
        self.assertEqual(value['before'], [2, 1, 0, 4, 3, 5])
        self.assertEqual(value['after'], [26, 27, 28, 24, 25, 23])
        self.assertEqual(value['sourceOffsets'], [3, 1, 0, 8, 6, 10])
        self.assertEqual(value['text'], '[\\-]\r\nY Z\nX')

    def test_recipe_title_and_editorial_notes_do_not_change_mathematical_evidence(self):
        root = self.fixture()
        path = root / 'experiments/records/lp2-row-column-routes/record.json'
        record = json.loads(path.read_bytes())
        record['title'] = 'Clearer route account'
        record['browser_followups'][0]['title'] = 'Clearer description of the same program'
        record['research_questions'][0]['note'] = 'Clearer explanation of the existing exclusion.'
        path.write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
        self.assertEqual(build(root, write=False), build(write=False))

    def test_archived_text_checker_and_report_changes_fail_their_source_pins(self):
        for name in ['text/lp2-00.txt', BASE + '/check.py', BASE + '/results.json']:
            with self.subTest(name=name):
                root = self.fixture()
                with (root / name).open('ab') as output:
                    output.write(b' changed')
                with self.assertRaisesRegex(ValueError, 'pin changed'):
                    build(root, write=False)

    def test_changed_current_input_or_recipe_mathematics_cannot_reuse_the_report(self):
        root = self.fixture()
        path = root / 'data/local-run-inputs.json'
        bundle = json.loads(path.read_bytes())
        next(p for p in bundle['pages'] if p['id'] == 'lp2-15')['raw'] += '\n'
        path.write_text(json.dumps(bundle, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Current browser inputs differ'):
            build(root, write=False)
        root = self.fixture()
        path = root / 'experiments/records/lp2-row-column-routes/record.json'
        record = json.loads(path.read_bytes())
        record['browser_followups'][0]['card']['method']['value']['operations'][1]['b'] = 27
        path.write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'mathematical definition'):
            build(root, write=False)

    def test_even_repinning_a_false_finite_witness_fails_original_independent_checker(self):
        root = self.fixture()
        path = root / BASE / 'results.json'
        report = json.loads(path.read_bytes())
        next(r for r in report['recipes'] if r['id'] == DECLARATION['id'])['pages'][0]['first_mismatch_zero_based'] = 3
        path.write_text(json.dumps(report, ensure_ascii=False), encoding='utf-8')
        with patch.dict(DECLARATION['sourceSha256'], {BASE + '/results.json': sha(path.read_bytes())}):
            with self.assertRaises(subprocess.CalledProcessError):
                build(root, write=False)

    def test_browser_arithmetic_bug_is_rejected_by_full_independent_python_output(self):
        root = self.fixture()
        path = root / 'local-experiment.js'
        code = path.read_text(encoding='utf-8')
        self.assertIn('step.a*index.get(ch)+step.b', code)
        path.write_text(code.replace('step.a*index.get(ch)+step.b', 'step.a*index.get(ch)+step.b+1'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Browser program and independent Python replay disagree'):
            build(root, write=False)


if __name__ == '__main__':
    unittest.main()
