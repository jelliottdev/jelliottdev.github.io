"""Copy only small exact evidence into one source-integrity control record."""
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT.parent / 'source-cache' / 'dukotah-cicada3301'
OUT = ROOT / 'experiments/records/dukotah-offset-model-integrity'
OUT.mkdir(parents=True, exist_ok=True)
REV = 'f08b20b632d91209ddbaa747e8e2f23df0c78ba1'
A = 'liber-primus/analysis/'
source_files = {
    'source-lib_padsweep.py': A + 'round17/lib_padsweep.py',
    'source-skipdecode.py': A + 'campaign18_skip/skipdecode.py',
    'source-gematria.py': 'liber-primus/src/lp/gematria.py',
    'source-lib_l6.py': A + 'round18/L6-offset-marsaglia/scripts/lib_l6.py',
    'source-control_offset.py': A + 'round18/L6-offset-marsaglia/scripts/control_offset.py',
    'source-audit_builders.py': A + 'round18/L6-offset-marsaglia/scripts/audit_builders.py',
    'source-sweep_offset.py': A + 'round18/L6-offset-marsaglia/scripts/sweep_offset.py',
    'source-capsule-manifest.json': 'liber-primus/handoff/capsule/MANIFEST.json',
    'source-control-offset.json': A + 'round18/L6-offset-marsaglia/out/control_offset.json',
    'source-checkpoint-A1-0.json': A + 'round18/L6-offset-marsaglia/out/ckpt_A1/0.json',
    'LICENSE.source': 'LICENSE',
}
for name, path in source_files.items():
    (OUT / name).write_bytes(subprocess.check_output(['git', '-C', str(SOURCE), 'show', f'{REV}:{path}']))
for name, target in {
    'kjv.txt': 'source-kjv.txt',
}.items():
    shutil.copyfile(HERE / 'corpora' / name, OUT / target)
for name in ('audit.json','control_offset.json','input-reconstruction.json','pilot-a1.json',
             'corpora-receipt.json','corpus-recovery-check.json','saved-check.json',
             'trigram-kjv-only.npy'):
    shutil.copyfile(HERE / name, OUT / name)
print('Packaged', len(source_files) + 1 + 8, 'evidence files in', OUT)
