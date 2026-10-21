"""Run the fixed 13-case pilot with the clean-build binary; save before judging.

The declared comparison is exact return codes, normalized diagnostics and
payload bytes against the archived guarded pilot, not hidden-data detection.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outguess', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    exe = args.outguess.resolve()
    build = json.loads((HERE/'clean-build-report.json').read_bytes())
    if sha(exe) != build['executable_sha256']:
        raise ValueError('Binary differs from the recorded clean build')
    plan = json.loads((HERE/'plan.json').read_bytes())
    old = {r['image']: r for r in json.loads((HERE/'results/report.json').read_bytes())['records']}
    args.output.mkdir(parents=False, exist_ok=False)
    rows = []
    for image in plan['images']:
        source = ROOT/image['path']
        if sha(source) != image['sha256']:
            raise ValueError('Changed input: '+image['id'])
        dest = args.output.resolve()/(image['id']+'.bin')
        try:
            proc = subprocess.run([str(exe), '-r', '-k', plan['key'], str(source), str(dest)],
                                  capture_output=True, timeout=plan['timeout_seconds'])
            code, diagnostic = proc.returncode, proc.stderr.decode('utf-8', errors='replace')
        except subprocess.TimeoutExpired as error:
            code, diagnostic = None, (error.stderr or b'').decode('utf-8', errors='replace')
        diagnostic = diagnostic.replace(str(source), image['path']).replace(str(dest), dest.name)
        previous = old[image['id']]
        payload_match = dest.is_file() and dest.read_bytes() == (HERE/'results'/previous['output']).read_bytes()
        row = {'image': image['id'], 'returncode': code, 'diagnostic': diagnostic,
               'bytes': dest.stat().st_size if dest.exists() else None,
               'sha256': sha(dest) if dest.exists() else None,
               'same_returncode': code == previous['returncode'],
               'same_diagnostic': diagnostic == previous['diagnostic'],
               'same_payload_bytes': payload_match}
        rows.append(row)
        if image['id'] in plan['controls'] and (code != 0 or row['sha256'] != plan['controls'][image['id']]):
            break
    result = {'schema': 'liberpedia-guarded-rebuild-comparison-v1',
              'tool_sha256': sha(exe), 'pilot_plan_sha256': sha(HERE/'plan.json'),
              'baseline_report_sha256': sha(HERE/'results/report.json'),
              'build_report_sha256': sha(HERE/'clean-build-report.json'), 'records': rows}
    (args.output/'comparison.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8', newline='\n')
    if len(rows) != 13 or not all(r[k] for r in rows for k in ('same_returncode','same_diagnostic','same_payload_bytes')):
        raise SystemExit('Comparison differs or stopped; inspect saved evidence')
    print('PASS: clean build reproduces all 13 return codes, diagnostics and payload byte streams')


if __name__ == '__main__':
    main()
