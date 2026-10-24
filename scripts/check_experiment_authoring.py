"""Check committed experiment authoring transitions without rewriting records."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SCHEMA = 'liberpedia-experiment-v2'


def event_base(name, event):
    """Use the whole push/PR, rather than only the last commit in a batch."""
    if name == 'push':
        value = event.get('before')
        if value == '0' * 40:  # New branch: its inherited history is not new work.
            return 'HEAD^'
    elif name == 'pull_request':
        pull = event.get('pull_request')
        base = pull.get('base') if isinstance(pull, dict) else None
        value = base.get('sha') if isinstance(base, dict) else None
    else:
        return 'HEAD^'
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{40}', value) or value == '0' * 40:
        raise ValueError('The GitHub event has no valid comparison commit.')
    return value


def fetch_baseline(root, base):
    """Fetch one absent event commit; do not download the repository history."""
    if not re.fullmatch(r'[0-9a-f]{40}', base):
        return
    try:
        git(root, 'cat-file', '-e', base + '^{commit}')
    except subprocess.CalledProcessError:
        git(root, 'fetch', '--no-tags', '--depth=1', 'origin', base)


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
    comparison = parser.add_mutually_exclusive_group()
    comparison.add_argument('--base', help='Available baseline commit (default: HEAD^).')
    comparison.add_argument('--github-event', action='store_true', help='Compare the entire push or pull request using the GitHub event.')
    parser.add_argument('--fetch-base', action='store_true', help='Fetch an absent event SHA from origin with depth 1.')
    args = parser.parse_args(argv)
    try:
        root = Path(__file__).resolve().parents[1]
        base = args.base or 'HEAD^'
        if args.github_event:
            event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
            if not isinstance(event, dict):
                raise ValueError('The GitHub event must be a JSON object.')
            base = event_base(os.environ.get('GITHUB_EVENT_NAME'), event)
        if args.fetch_base:
            fetch_baseline(root, base)
        count, errors = check(root, base)
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'Experiment authoring check failed: {error}', file=sys.stderr)
        return 1
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'Experiment authoring transitions: {count} committed records checked; PASS.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
