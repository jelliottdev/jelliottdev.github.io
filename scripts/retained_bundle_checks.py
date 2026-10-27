"""Run only pinned declared --check commands inside an extracted reproduction ZIP.

The grammar is deliberately smaller than a shell. A new unsupported command is
an error, never an excuse to omit a declared retained-output reproduction check.
"""
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import time

MAX_COMMANDS = 4
TIMEOUT = 120
MAX_FILE_BYTES = 8 * 1024 * 1024
HEX = re.compile(r'[a-f0-9]{64}')
COMMAND = re.compile(r'(python3?|node) +([A-Za-z0-9_./-]+) +--check(?: +([A-Za-z0-9_./-]+))?')


def _path(value):
    if (not isinstance(value, str) or not 1 <= len(value) <= 350
            or not re.fullmatch(r'[A-Za-z0-9_./-]+', value)
            or any(part in ('', '.', '..') for part in value.split('/'))):
        raise ValueError('Retained bundle checks need safe repository-relative paths')
    return value


def _digest(value):
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise ValueError('Retained bundle check needs an exact SHA-256 pin')
    return value


def parse_checks(record, inventory):
    """Return immutable token tuples, after binding every argument to inventory."""
    if not isinstance(record, dict) or not isinstance(inventory, dict):
        raise ValueError('Use a declared record and verified bundle inventory')
    if not any(record.get(name) for name in ('published_programs', 'published_program_collections')):
        raise ValueError('Retained bundle checks require a published declaration')
    reproduction = record.get('reproduction')
    if not isinstance(reproduction, dict):
        raise ValueError('Retained bundle checks need reproduction metadata')
    first = _path(reproduction.get('script'))
    first_sha = _digest(reproduction.get('script_sha256', record.get('script_sha256')))
    declared, output_paths = {first: first_sha}, set()
    for role in ('inputs', 'outputs'):
        pins = reproduction.get(role)
        if not isinstance(pins, list):
            raise ValueError('Retained bundle checks need declared input/output pins')
        seen = set()
        for pin in pins:
            if not isinstance(pin, dict):
                raise ValueError('Invalid retained bundle reproduction pin')
            path, digest = _path(pin.get('path')), _digest(pin.get('sha256'))
            if path in seen or path in declared and declared[path] != digest:
                raise ValueError('Duplicate or conflicting retained bundle pin')
            seen.add(path)
            declared[path] = digest
            if role == 'outputs':
                output_paths.add(path)
    command = reproduction.get('command')
    if not isinstance(command, str) or not 1 <= len(command) <= 2000 or any(ord(ch) < 32 for ch in command):
        raise ValueError('Use a bounded retained check command')
    segments = command.split('&&')
    if not 1 <= len(segments) <= MAX_COMMANDS:
        raise ValueError('Declare at most four retained check commands')
    result = []
    for ordinal, segment in enumerate(segments):
        parsed = COMMAND.fullmatch(segment.strip())
        if parsed is None:
            raise ValueError('Unsupported retained check command grammar')
        interpreter, script, output = parsed.groups()
        script = _path(script)
        if (ordinal == 0 and script != first
                or interpreter.startswith('python') and not script.endswith('.py')
                or interpreter == 'node' and not script.endswith(('.js', '.mjs', '.cjs'))):
            raise ValueError('Retained check interpreter or first script differs from reproduction')
        if output is not None:
            output = _path(output)
            if output not in output_paths:
                raise ValueError('Retained check argument must be a declared reproduction output')
        for path in (script, *([output] if output is not None else [])):
            member = inventory.get(path)
            if (path not in declared or not isinstance(member, dict) or member.get('path') != path
                    or member.get('sha256') != declared[path] or type(member.get('bytes')) is not int
                    or not 0 <= member['bytes'] <= MAX_FILE_BYTES):
                raise ValueError('Retained check script/output is absent or differs from pinned inventory: ' + path)
        result.append((interpreter, script, '--check', *([output] if output is not None else [])))
    return tuple(result)


def run_checks(root, record, inventory, *, run=subprocess.run, monotonic=time.monotonic):
    """Fail on missing dependencies, abnormal exit or a total120-second deadline.

    Commands are selected entirely before execution, with no shell. Pinned check
    programs remain ordinary reviewed reproduction code, not generated code.
    """
    commands = parse_checks(record, inventory)
    root = Path(root).resolve()
    # Recheck selected bytes in the extraction, not current repository copies.
    for command in commands:
        for path in (command[1], *command[3:]):
            target = (root / path).resolve()
            member = inventory[path]
            if not target.is_relative_to(root) or not target.is_file():
                raise ValueError('Retained check file escapes or is absent from extraction: ' + path)
            if target.stat().st_size != member['bytes']:
                raise ValueError('Retained check extracted file size changed: ' + path)
            digest, size = hashlib.sha256(), 0
            with target.open('rb') as source:
                for chunk in iter(lambda: source.read(65536), b''):
                    size += len(chunk)
                    if size > member['bytes']:
                        raise ValueError('Retained check extracted file grew beyond its pin: ' + path)
                    digest.update(chunk)
            if size != member['bytes'] or digest.hexdigest() != member['sha256']:
                raise ValueError('Retained check extracted file SHA-256 changed: ' + path)
    started = monotonic()
    results = []
    for interpreter, script, *arguments in commands:
        remaining = TIMEOUT - (monotonic() - started)
        if remaining <= 0:
            raise subprocess.TimeoutExpired(script, TIMEOUT)
        executable = sys.executable if interpreter.startswith('python') else 'node'
        try:
            results.append(run([executable, script, *arguments], cwd=root, shell=False,
                               capture_output=True, text=True, encoding='utf-8', check=True,
                               timeout=remaining, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}))
        except subprocess.CalledProcessError as error:
            if hasattr(error, 'add_note'):
                error.add_note('Isolated retained check output:\n' + (error.stdout or '') + (error.stderr or ''))
            raise
    return tuple(results)
