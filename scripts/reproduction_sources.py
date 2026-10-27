"""Resolve reviewed reproduction bytes without changing their original identity.

Canonical record.json dependencies and explicitly maintained implementation
modules may use their respective immutable archives. Scientific inputs and
result files never fall back to other versions.
"""
import hashlib
import re
from pathlib import Path
from archive_authored_sources import MANIFEST, MAX_SOURCE, entry, manifest_entries, parse
import archive_reproduction_code as code_archive

RECORD = re.compile(r'experiments/records/([a-z0-9]+(?:-[a-z0-9]+)*)/record\.json')
HEX = re.compile(r'[a-f0-9]{64}')


def _contained(root, name):
    if (not isinstance(name, str) or not name or len(name) > 500
            or not re.fullmatch(r'[a-zA-Z0-9_./-]+', name)
            or any(part in ('', '.', '..') for part in name.split('/'))):
        raise ValueError('Reproduction source path escapes repository or is unsafe')
    target = (root / name).resolve()
    if not target.is_relative_to(root):
        raise ValueError('Reproduction source escaped its repository')
    return target


def read_pinned(root, pin):
    """Return (reviewed bytes, derived repository-relative source path).

    The caller's pin has exactly path/sha256. A compiled source_path hint is
    deliberately not accepted as authority; callers must derive it again.
    """
    root = Path(root).resolve()
    if (not isinstance(pin, dict) or set(pin) != {'path', 'sha256'}
            or not isinstance(pin['sha256'], str) or not HEX.fullmatch(pin['sha256'])):
        raise ValueError('Use an exact reviewed reproduction pin')
    name, expected = pin['path'], pin['sha256']
    current = _contained(root, name)
    try:
        data = current.read_bytes()
    except FileNotFoundError:
        data = None
    if data is not None and hashlib.sha256(data).hexdigest() == expected:
        return data, name
    record = RECORD.fullmatch(name)
    if not record:
        if code_archive.maintained_path(name):
            try:
                allowed = code_archive.policy(root)
                if name in allowed:
                    manifest = code_archive.manifest_entries(code_archive.parse(
                        code_archive.bounded_read(root, code_archive.MANIFEST)))
                    if any(item['sourcePath'] not in allowed for item in manifest.values()):
                        raise ValueError('Retained code association is outside maintained policy')
                    retained = manifest.get((name, expected))
                    if retained is None:
                        raise ValueError('No exact retained maintained code version: ' + name)
                    return code_archive.read_entry(root, retained), retained['path']
            except FileNotFoundError as error:
                raise ValueError('A stale maintained code dependency needs its retained source manifest') from error
        raise ValueError('Reproduction source SHA-256 mismatch: ' + name)

    manifest_path = _contained(root, MANIFEST)
    try:
        if manifest_path.stat().st_size > MAX_SOURCE:
            raise ValueError('Source archive manifest exceeds its byte bound')
        manifest = manifest_entries(parse(manifest_path.read_bytes()))
    except FileNotFoundError as error:
        raise ValueError('A stale record dependency needs its retained source manifest') from error
    for item in manifest.values():
        if (not isinstance(item['recordId'], str) or len(item['recordId']) > 100
                or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', item['recordId'])):
            raise ValueError('Invalid retained source record association')
    retained = manifest.get(expected)
    if retained is None or retained['recordId'] != record.group(1):
        raise ValueError('No exact retained version for the reviewed record dependency: ' + name)
    target = _contained(root, retained['path'])
    try:
        if target.stat().st_size != retained['bytes']:
            raise ValueError('Retained source byte count changed')
        historical = target.read_bytes()
    except FileNotFoundError as error:
        raise ValueError('Retained source record is missing') from error
    if entry(historical) != retained:
        raise ValueError('Retained source bytes or record association changed')
    return historical, retained['path']
