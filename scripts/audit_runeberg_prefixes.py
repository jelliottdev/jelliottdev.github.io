"""Audit twelve pinned corpus prefixes, without running third-party code.

Pass a local clone of mortlach/project-runeberg. Git reads committed bytes,
not checkout files. A partial clone may fetch missing blobs from its remote.
--write saves the report; otherwise compare it with the published report.
This is an input audit, not a language significance test.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'a39e87ece3e6cbb0f00f7ad5fff9183da5c66d87'
REPORT = ROOT / 'exports/runeberg-prefix-audit.json'


def audit(repo):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args])
    alphabet = ''.join(a['rune'] for a in json.loads(
        (ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet'])
    names = sorted(git('ls-tree', '-z', '--name-only', REVISION + ':files')
                   .decode('utf-8').strip('\0').split('\0'))
    rows = []
    for name in names[:12]:
        raw = git('show', REVISION + ':files/' + name)
        tokens = [token for token in raw.decode('utf-8').split(' ') if token]
        prefix = tokens[:2902]
        outside = Counter(c for token in prefix for c in token if c not in alphabet)
        rows.append({
            'file': name, 'sha256': hashlib.sha256(raw).hexdigest(),
            'bytes': len(raw), 'tokens': len(tokens),
            'prefix_eligible': len(tokens) >= 2902,
            'prefix_non_alphabet': dict(sorted(outside.items())),
            'prefix_non_alphabet_tokens': sum(any(c not in alphabet for c in t) for t in prefix),
        })
    return {
        'revision': REVISION, 'file_count': len(names),
        'selection': 'First twelve filenames in Unicode lexical order',
        'prefix_tokens': 2902, 'alphabet': alphabet,
        'counting_rule': 'UTF-8 decode; split on literal space; discard empty tokens; count Unicode code points',
        'scope': 'Deterministic convenience sample, not random or representative; no corpus probabilities reproduced',
        'files': rows,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    report = audit(args.repository)
    if args.write:
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    else:
        assert report == json.loads(REPORT.read_text(encoding='utf-8')), 'Published report differs'
    print(f"PASS: {len(report['files'])} prefixes checked against pinned Git bytes")
    print(json.dumps({r['file']: r['prefix_non_alphabet'] for r in report['files']}))
