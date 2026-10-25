"""Published count projection identity and independent mismatch gates."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from build_published_count_evidence import BASE, REQUIRED, ROOT, build, sha, stable


class ProjectionTests(unittest.TestCase):
    def fixture(self):
        directory = tempfile.TemporaryDirectory(prefix='liberpedia-published-count-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        for name in REQUIRED + [f'{BASE}/record.json', 'data/local-run-inputs.json', 'local-experiment.js', 'scripts/build_published_count_evidence.py', 'data/published-count-evidence.json', 'published-count-evidence-data.js']:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)
        return root

    def update_result(self, root, change):
        path = root / BASE / 'results.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        change(data)
        path.write_text(json.dumps(data), encoding='utf-8')
        record_path = root / BASE / 'record.json'
        record = json.loads(record_path.read_text(encoding='utf-8'))
        record['published_count_evidence']['source_sha256'][f'{BASE}/results.json'] = sha(path.read_bytes())
        record_path.write_text(json.dumps(record), encoding='utf-8')

    def test_generated_artifacts_match_and_bind_every_output_and_original_source(self):
        manifest = build(write=False)
        self.assertEqual(len(manifest['entries']), 1)
        entry, record = manifest['entries'][0], manifest['records'][0]
        self.assertEqual(entry['caseId'], 'lag-six-hyphen-period--all-pages')
        self.assertEqual(len(entry['task']['pages']), 56)
        self.assertEqual(entry['run']['result']['wordPairs']['matches'], 77)
        self.assertEqual(entry['run']['result']['wordPairs']['opportunities'], 1267)
        self.assertEqual(entry['run']['result']['wordPairs']['expected'], {'numerator': '256123', 'denominator': '5720'})
        self.assertEqual(record['revision'], sha(stable(record['provenance'])))
        self.assertEqual(record['provenance']['projection']['taskId'], entry['task']['taskId'])
        self.assertEqual(record['provenance']['projection']['resultId'], entry['run']['id'])
        pins = {pin['path'] for pin in record['provenance']['sourcePins']}
        self.assertTrue(set(REQUIRED) <= pins)
        self.assertIn('not a historical browser submission', record['provenance']['dateMeaning'])
        code = "const D=require('./published-count-evidence-data.js'),E=require('./local-experiment.js'),c=require('node:crypto');const r=D.records[0],e=D.entries[0];if(!Object.isFrozen(e.run.result.wordPairs.pages)||c.createHash('sha256').update(E.stable(r.provenance)).digest('hex')!==r.revision||c.createHash('sha256').update(E.stable(e.run.result)).digest('hex')!==e.run.id)throw Error('Generated identity mismatch');"
        subprocess.run(['node', '-e', code], cwd=ROOT, check=True, capture_output=True)

    def test_title_changes_do_not_invalidate_immutable_projection(self):
        root = self.fixture()
        path = root / BASE / 'record.json'
        record = json.loads(path.read_text(encoding='utf-8'))
        record['title'] = 'Better reader-facing wording'
        record['browser_followups'][0]['title'] = 'Better recipe wording'
        path.write_text(json.dumps(record), encoding='utf-8')
        self.assertEqual(build(root, write=False), build(write=False))

    def test_changed_original_text_checker_and_result_bytes_fail_source_pins(self):
        for name in ['text/lp2-00.txt', f'{BASE}/check.py', f'{BASE}/results.json']:
            with self.subTest(name=name):
                root = self.fixture()
                with (root / name).open('ab') as output:
                    output.write(b' changed')
                with self.assertRaisesRegex(ValueError, 'source pin changed'):
                    build(root, write=False)

    def test_repinning_false_archived_page_statistics_does_not_make_them_evidence(self):
        root = self.fixture()
        self.update_result(root, lambda data: data['page_counts'][0].update(matches=data['page_counts'][0]['matches'] + 1))
        with self.assertRaisesRegex(ValueError, 'per-page statistics disagree'):
            build(root, write=False)

    def test_archived_float_is_checked_approximately_and_new_exact_mean_is_independently_computed(self):
        root = self.fixture()
        self.update_result(root, lambda data: data['target'].update(exact_word_shuffle_expected=45.7))
        with self.assertRaisesRegex(ValueError, 'Original totals disagree'):
            build(root, write=False)

    def test_changed_declaration_cannot_expand_the_projection(self):
        root = self.fixture()
        path = root / BASE / 'record.json'
        record = json.loads(path.read_text(encoding='utf-8'))
        record['published_count_evidence']['criterion']['boundaries'] = 'non-rune'
        path.write_text(json.dumps(record), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Unsupported published count projection'):
            build(root, write=False)

    def test_browser_engine_count_bug_is_rejected_by_independent_python(self):
        root = self.fixture()
        path = root / 'local-experiment.js'
        code = path.read_text(encoding='utf-8')
        self.assertIn('matches:wordMatches,', code)
        path.write_text(code.replace('matches:wordMatches,', 'matches:wordMatches+1,'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Browser engine and independent Python count disagree'):
            build(root, write=False)


if __name__ == '__main__':
    unittest.main()
