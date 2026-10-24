"""Cheap exact-byte probes; no semantic corpus substitution."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
targets = {'moby': '0670d7bb10b99d05f095a28942801aa74d4921d1b34dbdc76900e2c4c2bd2189',
           'pride': 'a5666f87abf2cbfdaa27ea8c73bd284da9649b9a2ab27b4e6c8f6aeab1bd1c88'}
rows = []
for name, wanted in targets.items():
    sources = [HERE / 'corpora' / f'{name}.txt']
    if name == 'pride':
        sources += list((HERE.parents[3].parent / 'source-cache/corpus-input-probes-20261023').glob('pride-*.txt'))
    for path in sources:
        raw = path.read_bytes()
        variants = {'raw': raw,
                    'lf': raw.replace(b'\r\n', b'\n'),
                    'crlf': raw.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'),
                    'bom-added': b'\xef\xbb\xbf' + raw,
                    'bom-stripped': raw.removeprefix(b'\xef\xbb\xbf'),
                    'one-final-lf': raw.rstrip() + b'\n'}
        rows.append({'name': name, 'path': str(path), 'variants': {
            label: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                    'matches_pinned': hashlib.sha256(data).hexdigest() == wanted}
            for label, data in variants.items()}})
assert not any(v['matches_pinned'] for row in rows for v in row['variants'].values())
(HERE / 'corpus-recovery-check.json').write_text(json.dumps({'checks': rows, 'exact_match_found': False}, indent=2)+'\n', encoding='utf-8', newline='\n')
print('No exact Moby/Pride source bytes among current files or simple newline/BOM variants')
