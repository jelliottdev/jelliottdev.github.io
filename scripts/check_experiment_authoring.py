"""Check committed experiment authoring transitions without rewriting records."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

SCHEMA = 'liberpedia-experiment-v2'


def validate_transition(previous, current):
    """Return authoring violations; published legacy records remain editable."""
    if not isinstance(current, dict):
        return ['The current record must be a JSON object.']
    if previous is not None and not isinstance(previous, dict):
        return ['The previous record must be a JSON object.']
    if current.get('schema') == SCHEMA:
        return []
    if previous is None:
        return [f'New records, including drafts, must declare schema {SCHEMA}.']
    if previous.get('schema') == SCHEMA:
        return [f'An existing {SCHEMA} record cannot be downgraded to legacy authoring.']
    if previous.get('status') == 'draft' and current.get('status') == 'published':
        return [f'Publishing a draft requires schema {SCHEMA}.']
    return []


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True).stdout


def check(root, base):
    try:
        baseline = git(root, 'rev-parse', '--verify', '--end-of-options', base + '^{commit}').decode().strip()
        head = git(root, 'rev-parse', '--verify', 'HEAD^{commit}').decode().strip()
    except subprocess.CalledProcessError as error:
        raise ValueError(f'Cannot resolve comparison base {base!r} and HEAD. Fetch the parent commit or pass --base with an available commit.') from error
    changed = git(root, 'diff', '--name-only', '--no-renames', '--diff-filter=ACMRT', '-z', baseline, head, '--', 'experiments/records').decode('utf-8').split('\0')
    errors, checked = [], 0
    for path in changed:
        if not re.fullmatch(r'experiments/records/[^/]+/record\.json', path):
            continue
        checked += 1
        try:
            current = json.loads(git(root, 'show', f'{head}:{path}'))
            exists = subprocess.run(['git', '-C', str(root), 'cat-file', '-e', f'{baseline}:{path}'], capture_output=True).returncode == 0
            previous = json.loads(git(root, 'show', f'{baseline}:{path}')) if exists else None
            errors.extend(f'{path}: {message}' for message in validate_transition(previous, current))
        except (ValueError, subprocess.CalledProcessError) as error:
            errors.append(f'{path}: Cannot read committed JSON: {error}')
    return checked, errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='HEAD^', help='Available baseline commit (default: HEAD^).')
    args = parser.parse_args(argv)
    try:
        count, errors = check(Path(__file__).resolve().parents[1], args.base)
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f'Experiment authoring check failed: {error}', file=sys.stderr)
        return 1
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'Experiment authoring transitions: {count} committed records checked; PASS.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
