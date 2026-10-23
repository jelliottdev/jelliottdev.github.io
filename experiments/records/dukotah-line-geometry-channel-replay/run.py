"""Run the pinned B-12 source programs in a disposable tree with verified images."""

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = HERE / 'source/liber-primus'
PLAN = HERE / 'source-replay-plan.json'
RECOVERY = REPO / 'research/source-intake/dukotah-image-input-recovery-2026-10-23.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compare_archived(a, b):
    state = {'float_differences': 0, 'max_float_abs_difference': 0.0,
             'nonfloat_differences': 0}
    def walk(x, y):
        if type(x) is not type(y):
            state['nonfloat_differences'] += 1
        elif isinstance(x, dict):
            if set(x) != set(y):
                state['nonfloat_differences'] += 1
            for key in set(x) & set(y):
                walk(x[key], y[key])
        elif isinstance(x, list):
            if len(x) != len(y):
                state['nonfloat_differences'] += 1
            for u, v in zip(x, y):
                walk(u, v)
        elif x != y:
            if isinstance(x, float):
                state['float_differences'] += 1
                state['max_float_abs_difference'] = max(
                    state['max_float_abs_difference'], abs(x-y))
            else:
                state['nonfloat_differences'] += 1
    walk(a, b)
    state['within_1e_10'] = (state['nonfloat_differences'] == 0 and
                            state['max_float_abs_difference'] < 1e-10)
    return state

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--summarize-only', action='store_true', help='reuse the two completed source JSON outputs')
    args = ap.parse_args()
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    assert sha(RECOVERY) == plan['inputs']['image_manifest']['sha256']
    for name, expected in plan['inputs'].items():
        if name == 'image_manifest':
            continue
        path = SOURCE / name
        assert sha(path) == expected, (name, sha(path), expected)
    rec = json.loads(RECOVERY.read_text(encoding='utf-8'))
    expected_images = {int(x['source_page'][1:-4]): x['source_expected_sha256']
                       for x in rec['lp2_source_images']}
    assert set(expected_images) == set(range(56))
    for n, expected in expected_images.items():
        assert sha(REPO / f'images/lp2-{n:02d}.jpg') == expected, n

    if not args.summarize_only:
        with tempfile.TemporaryDirectory(prefix='lp-b12-') as td:
            stage = pathlib.Path(td) / 'liber-primus'
            shutil.copytree(SOURCE, stage)
            dest = stage / 'data/relikd'
            dest.mkdir(parents=True, exist_ok=True)
            for n in range(56):
                shutil.copyfile(REPO / f'images/lp2-{n:02d}.jpg', dest / f'p{n}.jpg')
            lane = stage / 'analysis/round19/C3/l3'
            env = os.environ.copy()
            env['PYTHONUTF8'] = '1'
            env['OPENBLAS_NUM_THREADS'] = '1'
            for script in ('linegeom.py', 'linetests.py'):
                result = subprocess.run([sys.executable, script], cwd=lane, env=env,
                                        capture_output=True, text=True, timeout=600)
                if result.returncode:
                    raise RuntimeError(f'{script} failed: {result.stderr[-3000:]}')
                out = HERE / f'source-{script.removesuffix(".py")}.log'
                out.write_text(result.stdout, encoding='utf-8', newline='\n')
            for name in ('linegeom', 'linetests'):
                # Preserve JSON values while using stable LF bytes in the archive.
                payload = (lane / f'{name}.json').read_text(encoding='utf-8')
                (HERE / f'source-{name}.json').write_text(
                    payload, encoding='utf-8', newline='\n')

    stdout_hash = {f'{n}.py': sha(HERE / f'source-{n}.log')
                   for n in ('linegeom', 'linetests')}

    geom = json.loads((HERE / 'source-linegeom.json').read_text(encoding='utf-8'))
    tests = json.loads((HERE / 'source-linetests.json').read_text(encoding='utf-8'))
    archived = {}
    for name in ('linegeom', 'linetests'):
        key = f'analysis/round19/C3/l3/{name}.json'
        source_saved = REPO.parent / 'source-cache/dukotah-cicada3301/liber-primus' / key
        if source_saved.exists() and sha(source_saved) == plan['archived_outputs'][key]:
            archived[name] = json.loads(source_saved.read_text(encoding='utf-8'))
    channels = {k: {'separation_sigma': v['sep_sigma'], 'delta_bic': v['delta_bic'], 'pass': v['pass']}
                for k, v in geom['bimodality'].items() if v is not None}
    result = {
        'schema': 'liberpedia-b12-line-geometry-replay-v1',
        'plan_sha256': sha(PLAN),
        'source_revision': plan['source_revision'],
        'pages': 56,
        'image_sha256_digest': hashlib.sha256(''.join(expected_images[n]+'\n' for n in range(56)).encode()).hexdigest(),
        'source_outputs': {n: sha(HERE / f'source-{n}.json') for n in ('linegeom','linetests')},
        'source_stdout_sha256': stdout_hash,
        'source_archived_comparison': {n: compare_archived(obj, archived[n]) if n in archived else None
                                       for n, obj in (('linegeom',geom),('linetests',tests))},
        'image_rows': len(geom['rows']),
        'per_page_row_counts': [p['n_rows'] for p in geom['pages']],
        'channels': channels,
        'bit_decode': tests['bit_decode'],
        'control_C3': tests['control_C3'],
        'correlation': tests['correlation'],
        'justification_test': tests['justification_test'],
    }
    out = HERE / 'results.json'
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if args.check:
        assert out.read_text(encoding='utf-8') == encoded
    else:
        out.write_text(encoded, encoding='utf-8', newline='\n')
    print(json.dumps({'image_rows': result['image_rows'], 'archived_comparison': result['source_archived_comparison'],
                      'C3a_max_recovery': max(x['bit_recovery'] for x in tests['control_C3']['trials']),
                      'C3b': tests['control_C3']['decoder_validation']['verdict']}))

if __name__ == '__main__':
    main()
