"""Portable source controls and Part C target replay without modifying originals."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import engine as e


def scientific(value):
    if isinstance(value,dict):
        return {k:scientific(v) for k,v in value.items() if 'seconds' not in k}
    if isinstance(value,list):
        return [scientific(v) for v in value]
    return value


def main():
    plan=json.loads((e.HERE/'plan.json').read_text(encoding='utf8'))
    with tempfile.TemporaryDirectory(prefix='page-ramp-portable-') as temporary:
        target=Path(temporary)
        copied=target/e.HERE.relative_to(e.ROOT)
        shutil.copytree(e.HERE,copied,ignore=shutil.ignore_patterns('__pycache__'))
        for item in plan['inputs']:
            dest=target/item['path']
            if not dest.exists():
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(e.ROOT/item['path'],dest)
        def call(name):
            subprocess.run([sys.executable,str(copied/name)],cwd=target,check=True,capture_output=True,text=True)
        call('manifest.py')
        assert (copied/'key-manifest.json').read_bytes()==(e.HERE/'key-manifest.json').read_bytes()
        call('controls.py')
        assert scientific(json.loads((copied/'control-results.json').read_text()))==scientific(json.loads((e.HERE/'control-results.json').read_text()))
        shutil.copyfile(e.HERE/'control-results.json',copied/'control-results.json')
        call('check_controls.py')
        assert (copied/'control-check.json').read_bytes()==(e.HERE/'control-check.json').read_bytes()
        call('run.py')
        assert (copied/'cases.json').read_bytes()==(e.HERE/'cases.json').read_bytes()
        assert scientific(json.loads((copied/'results.json').read_text()))==scientific(json.loads((e.HERE/'results.json').read_text()))
    e.write(e.HERE/'replay-check.json',{'schema':'page-ramp-portable-replay-v1','source_cache_required':False,
            'all112plants_and_control_diagnoses_replayed':True,'all660target_cases_byte_identical':True,
            'all_scientific_report_fields_identical_except_timing':True,
            'original_frozen_plans_and_outputs_preserved':True})
    print('PASS portable112plants,independent controls,660targets;scientific outputs identical')


if __name__=='__main__':
    main()
