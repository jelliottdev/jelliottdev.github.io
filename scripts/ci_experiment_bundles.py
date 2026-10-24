"""Use conservative bundle selection for ordinary CI; manual/unknown runs stay full."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def command(event_name, event):
    argv = [sys.executable, str(ROOT / 'scripts/test_experiment_bundles.py')]
    if not isinstance(event, dict):
        return argv
    if event_name == 'push':
        base = event.get('before')
    elif event_name == 'pull_request':
        pull = event.get('pull_request')
        base_info = pull.get('base') if isinstance(pull, dict) else None
        base = base_info.get('sha') if isinstance(base_info, dict) else None
    else:
        return argv
    if (isinstance(base, str) and re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', base)
            and set(base) != {'0'}):
        argv.extend(['--changed-from', base])
    # The selector checks the actual Git baseline and dependency union. A shallow
    # checkout, changed shared code, or an unknown data input falls back to all.
    return argv


def main(env=None):
    env = os.environ if env is None else env
    try:
        event = json.loads(Path(env['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
    except (KeyError, OSError, ValueError):
        event = None
    argv = command(env.get('GITHUB_EVENT_NAME'), event)
    return subprocess.run(argv, cwd=ROOT, check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
