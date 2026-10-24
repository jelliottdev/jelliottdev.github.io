"""Offline, source-code replay of the KJV-only L6 control and one A1 unit.

This runs the pinned source files unchanged from a temporary source tree. It
does not recreate the unavailable four-book scorer or the complete target grid.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
FILES = {
    'source-gematria.py': 'src/lp/gematria.py',
    'source-score.py': 'src/lp/score.py',
    'source-ciphers.py': 'src/lp/ciphers.py',
    'source-stats.py': 'src/lp/stats.py',
    'source-corpus.py': 'src/lp/corpus.py',
    'source-run_stats.py': 'analysis/run_stats.py',
    'source-lib_numchannel.py': 'analysis/round11/lib_numchannel.py',
    'source-skipdecode.py': 'analysis/campaign18_skip/skipdecode.py',
    'source-lib_padsweep.py': 'analysis/round17/lib_padsweep.py',
    'source-null.py': 'benchmark/null.py',
    'source-lib_l6.py': 'analysis/round18/L6-offset-marsaglia/scripts/lib_l6.py',
    'source-control_offset.py': 'analysis/round18/L6-offset-marsaglia/scripts/control_offset.py',
    'source-sweep_offset.py': 'analysis/round18/L6-offset-marsaglia/scripts/sweep_offset.py',
    'source-b04-ks.py': 'analysis/round13/B04/ks.py',
    'source-b04-seeds.py': 'analysis/round13/B04/seeds.py',
    'source-b04-results_A.json': 'analysis/round13/B04/results_A.json',
    'source-b04-results_B.json': 'analysis/round13/B04/results_B.json',
    'source-b04-results_C.json': 'analysis/round13/B04/results_C.json',
    'source-kdf.py': 'analysis/round15/KDF/kdf.py',
    'source-kdf-results_A.json': 'analysis/round16/KDF/results_A.json',
    'source-prng_sweep.py': 'analysis/round16/prng/prng_sweep.py',
    'source-prng-results.json': 'analysis/round16/prng/results.json',
    'source-krisyotam_runes.txt': 'data/krisyotam_runes.txt',
    'source-english_quadgrams.txt': 'data/english_quadgrams.txt',
    'source-kjv.txt': 'data/kjv.txt',
    'trigram-kjv-only.npy': 'analysis/round17/trigram_idx.npy',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize(root):
    declared = {Path(row['path']).name: row['sha256'] for row in
                json.loads((HERE / 'record.json').read_text(encoding='utf-8'))['reproduction']['inputs']}
    for name, relative in FILES.items():
        source = HERE / name
        assert name in declared and digest(source) == declared[name], name
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    spec = importlib.util.spec_from_file_location('bundled_gematria', root / 'src/lp/gematria.py')
    gp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gp)
    pages = [gp.runes_to_indices(section) for section in
             (root / 'data/krisyotam_runes.txt').read_text(encoding='utf-8').split('%')]
    pages = [page for page in pages if page]
    ciphertext = bytes(index for page in pages[:-2] for index in page)
    receipt = json.loads((HERE / 'input-reconstruction.json').read_text(encoding='utf-8'))
    assert len(ciphertext) == receipt['length'] and hashlib.sha256(ciphertext).hexdigest() == receipt['sha256']
    target = root / 'analysis/seed_sweep/ct.bin'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(ciphertext)


def compare_control(root, scripts, env):
    subprocess.run([sys.executable, '-X', 'utf8', str(scripts / 'control_offset.py')],
                   cwd=scripts, env=env, check=True, stdout=subprocess.DEVNULL)
    new = json.loads((root / 'analysis/round18/L6-offset-marsaglia/out/control_offset.json').read_text(encoding='utf-8'))
    saved = json.loads((HERE / 'control_offset.json').read_text(encoding='utf-8'))
    new.pop('elapsed_s', None)
    saved.pop('elapsed_s', None)
    assert new == saved, 'fresh 40-control source output differs from saved KJV-only output'
    print('PASS: 40/40 source-control rows and summaries reproduce (elapsed time excluded)')


def compare_pilot(root, scripts, env):
    target = root / 'a1-unit0.json'
    code = ("import json,sys; import sweep_offset as S; "
            "S._init('A1'); result=S._unit_A1(S.jobs_for('A1')[0]); "
            "open(sys.argv[1],'w',encoding='utf-8').write(json.dumps(result))")
    subprocess.run([sys.executable, '-X', 'utf8', '-c', code, str(target)],
                   cwd=scripts, env=env, check=True)
    new = json.loads(target.read_text(encoding='utf-8'))
    saved = json.loads((HERE / 'pilot-a1.json').read_text(encoding='utf-8'))
    archive = json.loads((HERE / 'source-checkpoint-A1-0.json').read_text(encoding='utf-8'))
    assert new['i'] == saved['unit'] == 0 and new['n_offsets'] == saved['offsets'] == 1048576
    assert new['best'] == saved['best'] and new != archive
    assert new['best']['offset'] == 673662 and archive['best']['offset'] == 400310
    print('PASS: fresh 1,048,576-offset source unit reproduces the KJV-only winner 673,662; archived four-book winner is 400,310')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controls-only', action='store_true', help='skip the optional million-offset A1 unit')
    parser.add_argument('--pilot-only', action='store_true', help='run only the million-offset A1 unit (after a prior control replay)')
    args = parser.parse_args()
    if args.controls_only and args.pilot_only:
        parser.error('choose at most one of --controls-only and --pilot-only')
    with tempfile.TemporaryDirectory(prefix='lp-offset-model-') as folder:
        root = Path(folder) / 'liber-primus'
        materialize(root)
        scripts = root / 'analysis/round18/L6-offset-marsaglia/scripts'
        env = os.environ.copy()
        env['PYTHONUTF8'] = '1'
        if not args.pilot_only:
            compare_control(root, scripts, env)
        if not args.controls_only:
            compare_pilot(root, scripts, env)


if __name__ == '__main__':
    main()
