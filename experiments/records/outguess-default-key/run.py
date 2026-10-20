"""Run a bounded default-key retrieval sweep. Requires OutGuess; no network.

--output creates a new result directory; --check repeats all retrievals and
compares status, diagnostics and payload bytes with the saved run.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sha = lambda data: hashlib.sha256(data).hexdigest()

def sweep(executable, output):
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    records = []
    for image in plan['images']:
        source = ROOT / image['path']
        if sha(source.read_bytes()) != image['sha256']:
            raise ValueError('Image hash mismatch: '+image['id'])
        dest = output / (image['id']+'.bin')
        try:
            proc = subprocess.run([str(executable), '-r', '-k', plan['key'], str(source), str(dest)],
                                  capture_output=True, timeout=plan['timeout_seconds'])
            code, diagnostic = proc.returncode, proc.stderr.decode('utf-8', errors='replace')
        except subprocess.TimeoutExpired as error:
            code, diagnostic = None, (error.stderr or b'').decode('utf-8', errors='replace')
        # Only ephemeral path spellings are normalized; all other diagnostics remain.
        diagnostic = diagnostic.replace(str(source), image['path']).replace(str(dest), dest.name)
        payload = dest.read_bytes() if dest.exists() else None
        digest = sha(payload) if payload is not None else None
        expected = plan['controls'].get(image['id'])
        status = ('timeout' if code is None else 'control-match' if expected and code == 0 and digest == expected
                  else 'control-failed' if expected else 'candidate-output' if code == 0 and payload
                  else 'no-successful-retrieval')
        records.append({'image':image['id'],'image_sha256':image['sha256'],'returncode':code,
                        'status':status,'diagnostic':diagnostic,'output':dest.name if payload is not None else None,
                        'bytes':len(payload) if payload is not None else None,'sha256':digest})
    return {'schema':'liberpedia-outguess-sweep-v1','tool_sha256':sha(executable.read_bytes()),
            'plan_sha256':sha((HERE/'plan.json').read_bytes()),'records':records}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outguess',required=True)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output',type=Path)
    group.add_argument('--check',action='store_true')
    args=parser.parse_args()
    exe=Path(shutil.which(args.outguess) or args.outguess).resolve()
    if not exe.is_file():parser.error('OutGuess executable not found')
    if args.check:
        with tempfile.TemporaryDirectory(prefix='liberpedia-steg-') as tmp:
            result=sweep(exe,Path(tmp))
            saved=json.loads((HERE/'results/report.json').read_text(encoding='utf-8'))
            if result!=saved:raise SystemExit('Rerun differs; inspect tool version and diagnostics')
            for row in result['records']:
                if row['output'] and (Path(tmp)/row['output']).read_bytes() != (HERE/'results'/row['output']).read_bytes():
                    raise SystemExit('Payload bytes differ: '+row['image'])
        print('Every status, normalized diagnostic and payload byte reproduces.')
    else:
        args.output.mkdir(parents=False,exist_ok=False)
        result=sweep(exe,args.output)
        (args.output/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    from collections import Counter
    print(json.dumps(dict(Counter(r['status'] for r in result['records']))))
    if any(r['status'] in ('control-failed','timeout') for r in result['records']):
        raise SystemExit('Control failure or incomplete retrieval: do not interpret as a negative sweep')

if __name__=='__main__':main()
