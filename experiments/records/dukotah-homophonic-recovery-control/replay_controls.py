"""Stage and verify frozen controls with external texts; never overwrite expectations."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTPUTS = ['benchmark.json', 'case-11.json', 'case-23.json', 'case-37.json',
           'controls-results.json', 'independent-check.json']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def deterministic(value, path=()):
    if isinstance(value, dict):
        skip = {'benchmark', 'projected_seconds', 'seconds'} if not path else {'seconds'} if path[-1] == 'fit' else set()
        return {key: deterministic(item, path + (key,)) for key, item in value.items() if key not in skip}
    if isinstance(value, list):
        return [deterministic(item, path + (index,)) for index, item in enumerate(value)]
    return value


def first_difference(left, right, path='$'):
    if type(left) is not type(right):
        return path + ': JSON type differs'
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return path + ': fields differ'
        for key in left:
            difference = first_difference(left[key], right[key], path + '.' + key)
            if difference:
                return difference
    elif isinstance(left, list):
        if len(left) != len(right):
            return path + ': length differs'
        for index, (a, b) in enumerate(zip(left, right)):
            difference = first_difference(a, b, path + '[' + str(index) + ']')
            if difference:
                return difference
    elif left != right:
        return path + ': value differs'
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--inputs', type=Path, help='Prepared exact inputs with liber-primus/data/keys layout')
    inputs.add_argument('--from-git', type=Path, help='Read exact pinned blobs from a local source checkout')
    inputs.add_argument('--download', action='store_true', help='Explicitly download fixed pinned input URLs')
    parser.add_argument('--workdir', type=Path, required=True, help='New private work directory; must not exist')
    args = parser.parse_args()
    work = args.workdir.resolve()
    if work.exists() or not work.parent.is_dir():
        raise SystemExit('Choose a new work directory with an existing parent.')
    import numpy as np
    expected = {name: (HERE / name).read_bytes() for name in OUTPUTS}
    original_hashes = {name: sha(raw) for name, raw in expected.items()}
    plan = read(HERE / 'controls-plan-frozen.json')
    receipt = read(HERE / 'source-receipt.json')
    assert np.__version__ == read(HERE / 'controls-results.json')['numpy_version'], 'Use the recorded NumPy version; nothing is installed automatically.'
    assert sha((HERE / 'run_controls.py').read_bytes()) == plan['runner_sha256']
    assert sha((HERE / 'source-receipt.json').read_bytes()) == plan['source_receipt_sha256']
    assert sha((HERE / 'controls-plan-frozen.json').read_bytes()) == read(HERE / 'controls-results.json')['plan_sha256']
    stage_files = {name: (HERE / name).read_bytes() for name in
                   ['run_controls.py', 'check_controls.py', 'controls-plan-frozen.json', 'source-receipt.json']}
    for entry in receipt['files']:
        if not entry['source_path'].startswith('liber-primus/data/keys/'):
            raw = (HERE / entry['path']).read_bytes()
            assert len(raw) == entry['bytes'] and sha(raw) == entry['sha256'], entry['path']
            stage_files[entry['path']] = raw
    work.mkdir()
    preparation = [sys.executable, str(HERE / 'prepare_external_inputs.py'),
                   '--out', str(work / 'external-inputs')]
    if args.from_git:
        preparation += ['--from-git', str(args.from_git.resolve())]
    elif args.inputs:
        preparation += ['--from-directory', str(args.inputs.resolve())]
    else:
        preparation += ['--download']
    subprocess.run(preparation, check=True)
    for entry in receipt['files']:
        if entry['source_path'].startswith('liber-primus/data/keys/'):
            raw = (work / 'external-inputs' / entry['source_path']).read_bytes()
            assert len(raw) == entry['bytes'] and sha(raw) == entry['sha256'], entry['path']
            stage_files[entry['path']] = raw
    stage = work / 'isolated-controls'
    stage.mkdir()
    for name, raw in stage_files.items():
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    for name, raw in stage_files.items():
        assert (stage / name).read_bytes() == raw, 'Staging changed frozen bytes: ' + name
    environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    for name in ['run_controls.py', 'check_controls.py']:
        result = subprocess.run([sys.executable, str(stage / name)], cwd=stage,
                                capture_output=True, text=True, encoding='utf-8', env=environment)
        (work / (name + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8', newline='\n')
        print(result.stdout, end='', flush=True)
        if result.returncode:
            raise SystemExit(name + ' failed. Preserve this isolated directory and inspect its log.')
    verified = []
    for name in OUTPUTS:
        actual = read(stage / name)
        wanted = json.loads(expected[name])
        if name == 'independent-check.json':
            # This hash changes only because the raw result contains timings.
            assert actual['results_sha256'] == sha((stage / 'controls-results.json').read_bytes())
            assert wanted['results_sha256'] == original_hashes['controls-results.json']
            assert actual['checker_sha256'] == sha((stage / 'check_controls.py').read_bytes())
            actual = {key: value for key, value in actual.items() if key != 'results_sha256'}
            wanted = {key: value for key, value in wanted.items() if key != 'results_sha256'}
        difference = first_difference(deterministic(wanted), deterministic(actual))
        if difference:
            raise SystemExit('Deterministic replay mismatch in ' + name + ' ' + difference)
        verified.append(name)
    for name, before in expected.items():
        assert (HERE / name).read_bytes() == before, 'Expected bytes changed: ' + name
    verification = {'status': 'PASS', 'mode': 'local-git' if args.from_git else 'prepared-local' if args.inputs else 'explicit-download',
                    'plan_sha256': sha((HERE / 'controls-plan-frozen.json').read_bytes()),
                    'adapter_sha256': sha(Path(__file__).read_bytes()), 'numpy_version': np.__version__,
                    'staged_files_sha256': {name: sha(raw) for name, raw in stage_files.items()},
                    'compared_outputs': verified, 'comparison': 'Exact JSON types, values, arrays and flags; no floating tolerance.',
                    'excluded': ['Top-level benchmark timing samples, projected_seconds and total seconds; fit.seconds.',
                                 'Independent checker results_sha256 is recomputed against actual raw output, not compared across timing-varying reports.'],
                    'expected_output_sha256_unchanged': original_hashes,
                    'no_manuscript_target': True, 'no_expected_overwrite': True}
    (work / 'replay-receipt.json').write_text(json.dumps(verification, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS: all deterministic control outputs and independent checks match; expected bytes unchanged.', flush=True)


if __name__ == '__main__':
    main()
