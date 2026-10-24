"""Exercise draft creation in an isolated repository without modifying real records."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DraftTests(unittest.TestCase):
    def test_baseline_workflow(self):
        with tempfile.TemporaryDirectory(prefix='experiment-draft-', dir=ROOT.parent) as folder:
            root = Path(folder)
            (root / 'scripts').mkdir()
            shutil.copyfile(ROOT / 'scripts/new_experiment.py', root / 'scripts/new_experiment.py')
            records = root / 'experiments/records'
            original = ROOT / 'experiments/records/lp2-row-prime-sums/record.json'
            baseline = json.loads(original.read_text(encoding='utf-8'))
            base_dir = records / baseline['id']
            base_dir.mkdir(parents=True)
            (base_dir / 'record.json').write_bytes(original.read_bytes())

            def run(*args):
                return subprocess.run(
                    [sys.executable, str(root / 'scripts/new_experiment.py'), *args],
                    capture_output=True, text=True)

            result = run('new-variant', '--baseline', baseline['id'])
            self.assertEqual(result.returncode, 0, result.stderr)
            draft = json.loads((records / 'new-variant/record.json').read_text())
            self.assertEqual(draft['scope'], baseline['scope'])
            self.assertEqual(draft['family'], baseline['family'])
            self.assertEqual(draft['related'], [baseline['id']])
            self.assertEqual(draft['status'], 'draft')
            self.assertEqual(draft['schema'], 'liberpedia-experiment-v2')
            self.assertEqual(draft['result'], {'finding': '', 'limits': '', 'next_steps': ''})
            self.assertIsInstance(draft['analysis'], str)
            self.assertIn('## Plan before running', draft['analysis'])
            self.assertIn('#/experiments/' + baseline['id'], draft['analysis'])
            self.assertEqual({p.name for p in (records / 'new-variant').iterdir()}, {'record.json', 'run.py'})
            for key in ('summary', 'finding', 'limitations', 'next_steps', 'reader_finding',
                        'reader_limit', 'reader_question', 'article', 'article_path'):
                self.assertNotIn(key, draft)
            self.assertIn('record.json', result.stdout)
            self.assertIn('central publication', result.stdout)
            self.assertEqual(draft['review'], {'reviewer': '', 'retested_on': '', 'kind': '', 'human_review': 'pending'})
            self.assertEqual(draft['reproduction']['inputs'], [])
            self.assertEqual(draft['reproduction']['outputs'], [])
            self.assertEqual(draft['reproduction']['script_sha256'], '')
            stub = subprocess.run([sys.executable, str(records / 'new-variant/run.py')],
                                  capture_output=True, text=True)
            self.assertNotEqual(stub.returncode, 0)
            before = (records / 'new-variant/record.json').read_bytes()
            self.assertNotEqual(run('new-variant').returncode, 0)
            self.assertEqual((records / 'new-variant/record.json').read_bytes(), before)
            self.assertEqual((base_dir / 'record.json').read_bytes(), original.read_bytes())
            for invalid in ('missing', '../escape', 'new-variant'):
                self.assertNotEqual(run('rejected', '--baseline', invalid).returncode, 0)
                self.assertFalse((records / 'rejected').exists())
            self.assertEqual(run('independent').returncode, 0)
            independent = json.loads((records / 'independent/record.json').read_text())
            self.assertEqual(independent['family']['baseline'], 'independent')
            self.assertEqual(independent['scope']['pages'], [])
            self.assertEqual(independent['result'], {'finding': '', 'limits': '', 'next_steps': ''})
            self.assertEqual({p.name for p in (records / 'independent').iterdir()}, {'record.json', 'run.py'})
            # A v2 source carries prose only once; its result/review never becomes
            # the sibling's evidence, but all exact scope/family fields survive.
            v2 = json.loads(json.dumps(baseline))
            v2['id'] = 'v2-baseline'
            v2['schema'] = 'liberpedia-experiment-v2'
            v2['family']['baseline'] = v2['id']
            v2['result'] = {'finding': 'Prior result', 'limits': 'Prior limit', 'next_steps': 'Prior next'}
            v2['analysis'] = 'Prior analysis with \u03a9 and exact parameters.'
            for key in ('finding', 'limitations', 'next_steps', 'summary', 'article'):
                v2.pop(key, None)
            v2_path = records / v2['id'] / 'record.json'
            v2_path.parent.mkdir()
            v2_path.write_text(json.dumps(v2, ensure_ascii=False), encoding='utf-8')
            v2_before = v2_path.read_bytes()
            made = run('v2-sibling', '--baseline', v2['id'])
            self.assertEqual(made.returncode, 0, made.stderr)
            sibling = json.loads((records / 'v2-sibling/record.json').read_text(encoding='utf-8'))
            self.assertEqual(sibling['family'], v2['family'])
            self.assertEqual(sibling['scope'], v2['scope'])
            self.assertEqual(sibling['result'], {'finding': '', 'limits': '', 'next_steps': ''})
            self.assertNotIn('Prior analysis', sibling['analysis'])
            self.assertEqual(sibling['review'], {'reviewer': '', 'retested_on': '', 'kind': '', 'human_review': 'pending'})
            self.assertEqual(v2_path.read_bytes(), v2_before)
            for invalid_id in ('../escape', 'Upper-Case', 'bad_id'):
                self.assertNotEqual(run(invalid_id).returncode, 0)
            self.assertFalse((root / 'escape').exists())


if __name__ == '__main__':
    unittest.main()
