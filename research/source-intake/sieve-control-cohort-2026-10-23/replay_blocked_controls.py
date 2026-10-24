"""Re-attempt original finite entrypoints in a bounded isolated dependency copy."""
import hashlib, json, shutil, subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent
R = H.parents[2]
S = R.parent / 'source-cache/dukotah-cicada3301/liber-primus'
D = H / 'isolated-source/liber-primus'
dirs = ['src', 'benchmark', 'analysis/round19/I1', 'analysis/round19/I2',
        'analysis/round19/I3', 'analysis/round20/HITFN', 'analysis/round20/P3',
        'analysis/round18/L7-redteam', 'analysis/round21/L5-redteam-seal-and-notarerun',
        'analysis/round10b/B6-non-english-plaintext', 'analysis/campaign18_skip', 'analysis/round11',
        'analysis/round12/C1', 'analysis/round13/B04', 'analysis/round21/L1-fold-seal']
for rel in dirs:
    for p in (S / rel).rglob('*.py'):
        out = D / p.relative_to(S); out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, out)
for p in (S / 'analysis').glob('*.py'):
    out = D / p.relative_to(S); out.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(p, out)
files = ['data/english_quadgrams.txt', 'data/keys/self_reliance.txt',
         'data/keys/runepoem_oe.txt', 'SOLVED-PAGES.json', 'analysis/latin/latin_218.txt',
         'analysis/latin/latin_28233.txt', 'analysis/round20/P3/panelmax20.json',
         'analysis/round19/I3/calib19.json', 'data/krisyotam_runes.txt']
files += [str(p.relative_to(S)) for p in (S / 'analysis/round10b/B6-non-english-plaintext/corpora').glob('*.txt')]
for rel in files:
    if (S / rel).is_file():
        out = D / rel; out.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(S / rel, out)
recovered = R.parent / 'source-cache/corpus-input-probes-20261023/mabinogion-current.txt'
assert hashlib.sha256(recovered.read_bytes()).hexdigest() == '80dc6f0d8efc8398a2d1cc8cdf17237020c881cf4fbd2412dfa37ec8be19a5ed'
shutil.copyfile(recovered, D / 'data/keys/mabinogion.txt')
kjv = R / 'experiments/records/dukotah-offset-model-integrity/source-kjv.txt'
assert hashlib.sha256(kjv.read_bytes()).hexdigest() == '0f1a83cbcdc1d3fae6bcc3daaa496d4fa723fcce9526e84e20df12ae33fda986'
shutil.copyfile(kjv, D / 'data/kjv.txt')
checks = []
for name, script in [('hitfn', 'analysis/round20/HITFN/guard.py'),
                     ('l5', 'analysis/round21/L5-redteam-seal-and-notarerun/redteam21.py')]:
    result = subprocess.run([sys.executable, str(D / script)], capture_output=True, text=True, timeout=60)
    log = result.stdout + result.stderr
    (H / (name + '-after-english-recovery.txt')).write_text(log, encoding='utf-8')
    checks.append({'entrypoint': script, 'exit_code': result.returncode, 'log': name + '-after-english-recovery.txt',
                   'missing_welsh': 'welsh_mabinogion.txt' in log})
(H / 'blocked-controls.json').write_text(json.dumps(checks, indent=2) + '\n', encoding='utf-8')
print(json.dumps(checks))
