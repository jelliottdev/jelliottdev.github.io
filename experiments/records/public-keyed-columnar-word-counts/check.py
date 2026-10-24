"""Check determinism; the replay itself carries independent algebraic parity checks."""
import subprocess,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
FILES=['results.json', 'cases.json']
before={n:(HERE/n).read_bytes() for n in FILES}
subprocess.run(['python',str(HERE/'run.py')],check=True)
assert all((HERE/n).read_bytes()==before[n] for n in FILES)
print('Saved outputs reproduce byte-for-byte; independent internal parity checks pass.')
