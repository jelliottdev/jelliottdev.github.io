"""Losslessly repack one finite recipe, retaining exact source revisions first.

This changes storage only. It neither runs an experiment nor validates its
scientific finding. The ordinary research build still validates all controls.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

import archive_authored_sources as archive
import finite_control_storage as storage

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")


def prepare(root, record_id, followup_id):
    root = Path(root).resolve()
    if not all(type(v) is str and len(v) <= 100 and SLUG.fullmatch(v) for v in (record_id, followup_id)):
        raise ValueError('Use exact record and follow-up identifiers')
    path = (root / 'experiments/records' / record_id / 'record.json').resolve()
    if not path.is_relative_to(root) or path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError('Source record exceeds its location or size bound')
    raw = path.read_bytes()
    record = json.loads(raw.decode('utf-8-sig'))
    if record.get('id') != record_id or record.get('status') != 'published':
        raise ValueError('Use the exact published source record')
    matches = [r for r in record.get('browser_followups', []) if r.get('id') == followup_id]
    if len(matches) != 1 or matches[0].get('kind') != 'finite-settings':
        raise ValueError('Use one declared finite follow-up')
    original = matches[0]['control']
    before = storage.stable(storage.expand(original))
    packed = storage.compact_pooled(original)
    if packed.get('kind') != 'finite-program-controls-pooled-v1' or storage.stable(storage.expand(packed)) != before:
        raise ValueError('Repacking changed the expanded controls')
    updated = copy.deepcopy(record)
    next(r for r in updated['browser_followups'] if r['id'] == followup_id)['control'] = packed
    if updated == record:
        output = raw
    else:
        output = (json.dumps(updated, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if len(output) > 2 * 1024 * 1024:
        raise ValueError('Repacked source exceeds its size bound')
    report = {'recordId': record_id, 'followupId': followup_id, 'beforeBytes': len(raw),
              'afterBytes': len(output), 'expandedControlsSha256': hashlib.sha256(before.encode('utf-8')).hexdigest(),
              'sourceSha256': hashlib.sha256(raw).hexdigest(), 'changed': output != raw, 'written': False, 'targetExecutions': 0}
    return path, output, report


def repack(root, record_id, followup_id, *, write=False):
    path, output, report = prepare(root, record_id, followup_id)
    if write:
        # Archive the exact currently published bytes before replacing them.
        archive.build(root, write=True)
        if hashlib.sha256(path.read_bytes()).hexdigest() != report['sourceSha256']:
            raise ValueError('The source changed during repacking; nothing was replaced')
        if report['changed']:
            temp = None
            try:
                with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.repack-', suffix='.tmp', delete=False) as handle:
                    temp = Path(handle.name)
                    handle.write(output)
                os.replace(temp, path)
            finally:
                if temp is not None and temp.exists():
                    temp.unlink()
        archive.build(root, write=True)
        report['written'] = True
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', required=True)
    parser.add_argument('--followup', required=True)
    parser.add_argument('--write', action='store_true', help='Archive both revisions and atomically replace the source')
    args = parser.parse_args()
    print(json.dumps(repack(ROOT, args.record, args.followup, write=args.write)))
