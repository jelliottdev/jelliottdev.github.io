"""Freeze bounded local LENGTH replay before executing target measurements."""
import hashlib, json, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[3] / 'source-cache/dukotah-cicada3301'
REV = 'f08b20b632d91209ddbaa747e8e2f23df0c78ba1'
files = ['liber-primus/analysis/skeleton/length_anomaly.py',
         'liber-primus/src/lp/gematria.py', 'liber-primus/data/krisyotam_runes.txt',
         'liber-primus/data/kjv.txt']
files += [p.relative_to(SOURCE).as_posix() for p in sorted((SOURCE/'liber-primus/data/keys').glob('*.txt'))]
pins = []
for name in files:
    raw = (SOURCE/name).read_bytes()
    if name.endswith('/kjv.txt'):
        assert hashlib.sha256(raw).hexdigest() == '0f1a83cbcdc1d3fae6bcc3daaa496d4fa723fcce9526e84e20df12ae33fda986'
        provenance = 'Previously recovered local bytes; matches handoff/capsule/MANIFEST.json corpus.kjv pin (see existing dukotah-offset-model-integrity receipt).'
    else:
        committed = subprocess.check_output(['git', '-C', str(SOURCE), 'show', f'{REV}:{name}'])
        assert raw == committed, name
        provenance = 'Exact committed git bytes at source_revision.'
    pins.append({'path': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'provenance': provenance})
plan = dict(schema='liberpedia-hint-scope-local-plan-v1', source_revision=REV,
    source_ids=['F-02','B-06','B-07','B-15','B-19','B-20','B-24','C-01'],
    purpose='Initial entry review and a new bounded LENGTH measurement; source review is not method closure.',
    execution='Execute exact pinned length_anomaly.enc and words_of; source passage-index sampling and minimum 2*n candidate rule. Test both observed upper mean and all-F-null lower mean. Independently recount every sampled passage in check.py.',
    controls=['PARABLE: exact 20 word lengths before target calls', 'constant-4/constant-5 synthetic passage threshold checks before target calls'],
    omissions=['No substitute DIRECTION quadgram model: seed_sweep/ngram.bin absent.', 'No network fetch, archive hunt, full Gutenberg, huge seed sweep, or new language model.'],
    interpretation='Local subset replay, not recovery of the missing 47-text corpus or an inferential p-value. Existing archived LENGTH output was visible before this plan.',
    inputs=pins)
out = HERE/'plan-frozen.json'
assert not out.exists(), 'Plan already frozen'
out.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
print('Frozen', len(pins), 'exact git-byte input pins')
