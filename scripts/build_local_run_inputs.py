"""Generate a compact exact-text input bundle for bounded browser/Worker tasks.

No transcriptions are normalized or repaired, and no experiments are executed.
Run with --check to reject a missing or stale aggregate without writing it.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path('data/local-run-inputs.json')
SCHEMA = 'liberpedia-local-inputs-v1'
PAGE_IDS = tuple('lp1-' + str(n).zfill(2) for n in range(17)) + tuple(
    'lp2-' + str(n).zfill(2) for n in range(58))
MAX_BYTES = 2_000_000


def require(condition, message):
    if not condition:
        raise ValueError('local-run-inputs: ' + message)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def render(root=ROOT):
    root = Path(root)
    index = read(root / 'data/index.json')
    require(isinstance(index.get('pages'), list)
            and [p.get('id') for p in index['pages']] == list(PAGE_IDS),
            'index must list all 75 canonical page IDs in order')
    source_alphabet = index.get('alphabet')
    require(isinstance(source_alphabet, list) and len(source_alphabet) == 29,
            'index must contain the ordered 29-rune alphabet')
    alphabet, seen = [], set()
    for entry in source_alphabet:
        require(isinstance(entry, dict) and all(key in entry for key in ('rune', 'latin', 'prime')),
                'alphabet entry lacks a required field')
        rune, latin, prime = (entry[key] for key in ('rune', 'latin', 'prime'))
        require(isinstance(rune, str) and len(rune) == 1 and not rune.isspace()
                and not 0xD800 <= ord(rune) <= 0xDFFF and rune not in seen,
                'alphabet runes must be distinct Unicode characters')
        require(isinstance(latin, str) and 1 <= len(latin) <= 8
                and type(prime) is int and 2 <= prime <= 1000000, 'invalid alphabet label or prime')
        seen.add(rune)
        alphabet.append({'rune': rune, 'latin': latin, 'prime': prime})
    pages = []
    for identifier in PAGE_IDS:
        page = read(root / 'data/pages' / (identifier + '.json'))
        require(page.get('id') == identifier and isinstance(page.get('raw'), str),
                'missing or mismatched raw page: ' + identifier)
        reviewed = page.get('reviewed_text')
        require(reviewed is None or isinstance(reviewed, str),
                'reviewed_text must be null or exact text: ' + identifier)
        pages.append({'id': identifier, 'raw': page['raw'], 'reviewed_text': reviewed})
    data = (json.dumps({'schema': SCHEMA, 'alphabet': alphabet, 'pages': pages},
                       ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')
    require(len(data) < MAX_BYTES, 'aggregate must remain below 2 MB')
    return data


def build(root=ROOT, check=False):
    root = Path(root)
    data = render(root)
    output = root / OUTPUT
    unchanged = output.exists() and output.read_bytes() == data
    if check:
        require(unchanged, 'generated aggregate is missing or stale; run scripts/build_local_run_inputs.py')
    elif not unchanged:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        data = build(check=args.check)
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, str(error) + '\n')
    print(('Checked' if args.check else 'Built') + ' exact local-run inputs: 75 pages, '
          + str(len(data)) + ' UTF-8 bytes')


if __name__ == '__main__':
    main()
