"""Run pinned L6 control with its missing ct.bin supplied from the pinned rune parser.

The original PRNG helper imports analysis/seed_sweep/ct.bin eagerly although the L6
control uses only its generator. This wrapper supplies exactly the 12,956 indices
that lib_padsweep.nc.unsolved() also uses, without writing into the source tree.
"""
from pathlib import Path
import hashlib
import json
import runpy
import sys

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT.parent / 'source-cache' / 'dukotah-cicada3301'
SCRIPTS = SOURCE / 'liber-primus/analysis/round18/L6-offset-marsaglia/scripts'
sys.path.insert(0, str(SCRIPTS))
import lib_l6 as X  # noqa: E402

ct = bytes(int(x) for x in X.L.nc.unsolved())
assert len(ct) == 12956 and max(ct) < 29
expected = SOURCE / 'liber-primus/analysis/seed_sweep/ct.bin'
original_read = Path.read_bytes


def source_read(path):
    if path == expected:
        return ct
    return original_read(path)


Path.read_bytes = source_read
X.OUT = str(Path(__file__).resolve().parent)
(Path(X.OUT) / 'input-reconstruction.json').write_text(
    json.dumps({'input': 'analysis/seed_sweep/ct.bin',
                'source': 'lib_padsweep.nc.unsolved()',
                'length': len(ct), 'sha256': hashlib.sha256(ct).hexdigest()}, indent=2) + '\n',
    encoding='utf-8', newline='\n')
runpy.run_path(str(SCRIPTS / 'control_offset.py'), run_name='__main__')
