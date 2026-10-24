"""Explicitly obtain pinned external texts; no network unless --download is set."""
import argparse
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIN = 'f08b20b632d91209ddbaa747e8e2f23df0c78ba1'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--from-git', type=Path, help='Local source checkout; git show preserves pinned blob bytes')
    mode.add_argument('--from-directory', type=Path, help='Directory containing the exact liber-primus/data/keys paths')
    mode.add_argument('--download', action='store_true', help='Explicitly fetch fixed raw.githubusercontent.com pinned URLs')
    parser.add_argument('--out', type=Path, required=True, help='New private external-input directory; never overwritten')
    args = parser.parse_args()
    target = args.out.resolve()
    if target.exists() or not target.parent.is_dir():
        raise SystemExit('Choose a new output directory with an existing parent.')
    manifest = json.loads((HERE / 'source-receipt.json').read_bytes())
    required = [entry for entry in manifest['files'] if entry['source_path'].startswith('liber-primus/data/keys/')]
    fetched = []
    for entry in required:
        path = entry['source_path']
        if args.from_git:
            raw = subprocess.check_output(['git', '-C', str(args.from_git.resolve()), 'show', PIN + ':' + path])
        elif args.from_directory:
            raw = (args.from_directory.resolve() / path).read_bytes()
        else:
            url = 'https://raw.githubusercontent.com/Dukotah/cicada3301/' + PIN + '/' + path
            with urllib.request.urlopen(url, timeout=30) as response:
                raw = response.read(entry['bytes'] + 1)
        if len(raw) != entry['bytes'] or hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise SystemExit('Exact input hash/size mismatch: ' + path)
        fetched.append((entry, raw))
    # Validate all bytes before creating the output; do not modify expected results.
    target.mkdir()
    for entry, raw in fetched:
        file = target / entry['source_path']
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(raw)
    receipt = {'source_revision': PIN, 'mode': 'download' if args.download else 'local-git' if args.from_git else 'local-directory',
               'files': [{'path': entry['source_path'], 'sha256': entry['sha256'], 'bytes': len(raw)} for entry, raw in fetched]}
    (target / 'INPUTS-VERIFIED.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('Verified four pinned external text files in', target)


if __name__ == '__main__':
    main()
