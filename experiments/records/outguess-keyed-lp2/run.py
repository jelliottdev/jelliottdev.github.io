"""Bounded keyed OutGuess 0.13b retrieval on original LP2 JPEG bytes.

The named keys are a frozen probe, not an exhaustive dictionary. A zero exit
or an output file alone does not establish a hidden message.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SHA = lambda blob: hashlib.sha256(blob).hexdigest()


def invoke(exe, argv, output, timeout):
    try:
        proc = subprocess.run([str(exe), *argv, str(output)], capture_output=True, timeout=timeout)
        return proc.returncode, proc.stderr.decode('utf-8', errors='replace')
    except subprocess.TimeoutExpired as exc:
        return None, (exc.stderr or b'').decode('utf-8', errors='replace')


def controls(plan, exe, directory):
    cover = HERE / plan['plant']['cover']['path']
    payload = HERE / plan['plant']['payload']['path']
    assert SHA(cover.read_bytes()) == plan['plant']['cover']['sha256']
    assert SHA(payload.read_bytes()) == plan['plant']['payload']['sha256']
    rows = []
    for i, key in enumerate(plan['keys']):
        carrier_item = plan['plant']['carriers'][i]
        assert carrier_item['key'] == key
        carrier = HERE / carrier_item['path']
        assert SHA(carrier.read_bytes()) == carrier_item['sha256']
        for j, trial_key in enumerate(plan['keys']):
            destination = directory / f'plant-{i}-{j}.bin'
            code, diagnostic = invoke(exe, ['-r', '-k', trial_key, str(carrier)], destination,
                                      plan['timeout_seconds'])
            blob = destination.read_bytes() if destination.exists() else None
            matched = blob == payload.read_bytes()
            rows.append({'planted_key':key,'retrieval_key':trial_key,'returncode':code,
                         'payload_match':matched,'output_bytes':len(blob) if blob is not None else None,
                         'output_sha256':SHA(blob) if blob is not None else None})
            if matched != (i == j):
                raise RuntimeError(f'Planted control failed: {key!r} / {trial_key!r}')
    return rows


def retrieve(task, plan, exe, directory):
    key, image = task
    source = ROOT / image['path']
    destination = directory / f"{image['id']}-{plan['keys'].index(key)}.bin"
    code, diagnostic = invoke(exe, ['-r', '-k', key, str(source)], destination,
                              plan['timeout_seconds'])
    blob = destination.read_bytes() if destination.exists() else None
    diagnostic = diagnostic.replace(str(source), image['path']).replace(str(destination), destination.name)
    return {'image':image['id'],'key':key,'returncode':code,
            'status':'timeout' if code is None else 'output-unverified' if code == 0 and blob else 'no-retrieval',
            'output':destination.name if blob is not None else None,
            'bytes':len(blob) if blob is not None else None,
            'sha256':SHA(blob) if blob is not None else None,'diagnostic':diagnostic}


def run(plan, exe, directory):
    if SHA(exe.read_bytes()) != plan['tool_sha256']:
        raise RuntimeError('OutGuess binary hash differs')
    for image in plan['images']:
        if SHA((ROOT / image['path']).read_bytes()) != image['sha256']:
            raise RuntimeError('Original JPEG hash differs: ' + image['id'])
    with tempfile.TemporaryDirectory(prefix='outguess-controls-') as temp:
        positive = controls(plan, exe, Path(temp))
    tasks = [(key, image) for key in plan['keys'] for image in plan['images']]
    with ThreadPoolExecutor(max_workers=plan['workers']) as pool:
        rows = list(pool.map(lambda task: retrieve(task, plan, exe, directory), tasks))
    return {'schema':'liberpedia-outguess-keyed-lp2-v1','plan_sha256':SHA((HERE/'plan.json').read_bytes()),
            'tool_sha256':plan['tool_sha256'],'controls':positive,'rows':rows,
            'status_counts':dict(sorted(Counter(r['status'] for r in rows).items()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outguess',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf8'))
    args.output_dir.mkdir(parents=True,exist_ok=True)
    report = run(plan,args.outguess.resolve(),args.output_dir)
    saved = HERE/'results.json'
    if args.check:
        if report != json.loads(saved.read_text(encoding='utf8')):
            raise SystemExit('Rerun differs from saved result')
    else:
        if saved.exists(): raise SystemExit('Refusing to replace existing results')
        saved.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({'cases':len(report['rows']),'status_counts':report['status_counts']}))


if __name__ == '__main__': main()
