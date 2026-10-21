"""Audit pinned Git tree identities and duplicate witnesses, not corpus probabilities.

Reads committed source metadata and one blob per duplicate group. A partial
clone may fetch those blobs. Never executes code from the source repository.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'a39e87ece3e6cbb0f00f7ad5fff9183da5c66d87'


def audit(repository):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repository), *args])
    tree = git('ls-tree', '-r', '-z', REVISION)
    groups = defaultdict(list)
    other = []
    for item in tree.split(b'\0'):
        if not item:
            continue
        metadata, path = item.split(b'\t', 1)
        mode, kind, oid = metadata.decode('ascii').split()
        name = path.decode('utf-8')
        if name.startswith('files/'):
            assert kind == 'blob' and mode in ('100644', '100755')
            groups[oid].append(name)
        else:
            other.append({'path': name, 'kind': kind, 'object_id': oid})
    duplicate_groups = []
    for oid, names in sorted(groups.items()):
        if len(names) < 2:
            continue
        raw = git('cat-file', 'blob', oid)
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == oid
        tokens = [t for t in raw.decode('utf-8').split(' ') if t]
        duplicate_groups.append({'object_id': oid, 'paths': sorted(names),
                                 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                                 'tokens': len(tokens), 'eligible_2902_prefix': len(tokens) >= 2902})
    report = {'revision': REVISION, 'tree_listing_sha256': hashlib.sha256(tree).hexdigest(),
              'scope': 'All committed files/ paths for object-identity inventory; only duplicate-group blobs decoded. No full corpus statistics or conversion provenance reconstructed.',
              'token_rule': 'UTF-8 decode; split on literal space; discard empty tokens; prefix eligibility requires at least 2902 tokens',
              'file_entries': sum(map(len, groups.values())), 'distinct_blob_ids': len(groups),
              'excess_entries_over_distinct_blobs': sum(len(v)-1 for v in groups.values()),
              'other_tree_entries': other, 'duplicate_groups': duplicate_groups,
              'eligible_duplicate_excess_entries': sum(len(g['paths'])-1 for g in duplicate_groups if g['eligible_2902_prefix']),
              'limits': 'Object identity is a byte-level check, not a same-work or same-edition detector. Eligibility and language of all distinct texts are not audited. Removing duplicates would be a new sampling variant.'}
    return tree, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    tree, report = audit(args.repository)
    tree_path = ROOT/'exports/sources/runeberg-tree.bin'
    report_path = ROOT/'exports/runeberg-inventory.json'
    if args.write:
        tree_path.write_bytes(tree)
        report_path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    else:
        assert tree_path.read_bytes() == tree
        assert json.loads(report_path.read_bytes()) == report
    print(f"PASS: {report['file_entries']} entries, {report['distinct_blob_ids']} distinct blobs, {len(report['duplicate_groups'])} duplicate groups")
