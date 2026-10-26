"""Downloaded runner checks cover named opening mathematics on invented inputs."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import research_runner as runner
import verify_plan_controls as guard


class NamedOpeningGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        code = """const fs=require('fs'),E=require('./local-experiment.js'),C=require('./local-plan-controls.js');
        (async()=>{const alphabet=JSON.parse(fs.readFileSync('data/local-run-inputs.json','utf8')).alphabet;
        const task=await E.prepare({title:'Invented guard target',alphabet,pages:[{id:'lp2-00',text:alphabet.slice(0,4).map(v=>v.rune).join('')}],steps:[{op:'affine',a:1,b:1}],criterion:{kind:'exact-prefix-set',openings:[{id:'first',values:[1,2]},{id:'second',values:[28]}]}});
        console.log(JSON.stringify({task,suite:await C.prepare(task)}));})().catch(e=>{console.error(e);process.exitCode=1;});"""
        value = json.loads(subprocess.check_output(['node', '-e', code], cwd=ROOT, encoding='utf-8'))
        cls.task, cls.suite = value['task'], value['suite']

    def test_actual_browser_suite_passes_independent_download_guard_without_target_execution(self):
        original = runner.run
        def synthetic_only(task, *args, **kwargs):
            self.assertNotEqual(task['taskId'], self.task['taskId'])
            self.assertIn('synthetic', task['title'].lower())
            return original(task, *args, **kwargs)
        with patch.object(runner, 'run', side_effect=synthetic_only):
            self.assertEqual(guard.verified_controls(self.task, self.suite), 2)

    def test_changed_suite_identity_criterion_or_complete_result_hash_rejects(self):
        for alter in (lambda s: s.update(targetId='0' * 64),
                      lambda s: s['cases'][0].update(expectedResultSha256='0' * 64),
                      lambda s: s['cases'][0]['task']['criterion']['openings'].reverse()):
            value = copy.deepcopy(self.suite)
            alter(value)
            with self.subTest(alter=alter), self.assertRaises((ValueError, KeyError)):
                guard.verified_controls(self.task, value)

    def test_an_always_negative_named_opening_runner_fails_the_positive_control(self):
        original = runner.run
        def broken(task, *args, **kwargs):
            value = original(task, *args, **kwargs)
            for match in value['matches']:
                match['matched'], match['matchingOpenings'] = False, []
            return value
        with patch.object(runner, 'run', side_effect=broken), self.assertRaises(ValueError):
            guard.verified_controls(self.task, self.suite)


if __name__ == '__main__':
    unittest.main()
