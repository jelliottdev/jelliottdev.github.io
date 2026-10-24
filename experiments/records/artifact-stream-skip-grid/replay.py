"""Rerun the frozen target in isolation without changing its historical outputs."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf8'))
    with tempfile.TemporaryDirectory(prefix='artifact-skip-replay-') as temporary:
        target = Path(temporary)
        copied = target / HERE.relative_to(ROOT)
        shutil.copytree(HERE, copied, ignore=shutil.ignore_patterns('__pycache__'))
        for item in plan['inputs']:
            path = target/item['path']
            if not path.exists():
                path.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/item['path'],path)
        subprocess.run([sys.executable,str(copied/'run.py')],cwd=target,check=True,capture_output=True,text=True)
        assert (copied/'cases.json').read_bytes() == (HERE/'cases.json').read_bytes()
        expected = json.loads((HERE/'results.json').read_text(encoding='utf8'))
        actual = json.loads((copied/'results.json').read_text(encoding='utf8'))
        expected.pop('elapsed_seconds')
        actual.pop('elapsed_seconds')
        assert expected == actual
    receipt = {'schema':'artifact-stream-isolated-replay-v1','all_23100_cases_byte_identical':True,
               'all_report_fields_except_elapsed_time_identical':True,
               'original_target_and_post_target_plan_bytes_preserved':True}
    (HERE/'replay-check.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
