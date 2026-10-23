"""Replay the fixed 43-key Vigenere list in a public failed-attempt archive."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ALPHABET = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
LOOKUP = {r: i for i, r in enumerate(ALPHABET)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(stream, key):
    return [(c - key[i % len(key)]) % 29 for i, c in enumerate(stream)]


def run():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    openings_path = ROOT / 'experiments/records/lp2-known-vigenere-keys/plan.json'
    openings = json.loads(openings_path.read_text(encoding='utf-8'))['openings']
    keys = [[LOOKUP[c] for c in item['runes']] for item in plan['keys']]
    assert len(keys) == 43 and all(keys)
    assert len(set(tuple(k) for k in keys)) == 43
    anchor = [LOOKUP[c] for c in plan['source_output_anchor']['first_nine_runes']]
    cases, sources = [], []
    for page_number in range(56):
        page = f'lp2-{page_number:02d}'
        path = ROOT / 'text' / f'{page}.txt'
        raw = path.read_text(encoding='utf-8')
        stream = [LOOKUP[c] for c in raw if c in LOOKUP]
        sources.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path),
                        'runes': len(stream)})
        for item, key in zip(plan['keys'], keys):
            output = decode(stream, key)
            if page == 'lp2-15' and item['id'] == 'key-01':
                assert output[:9] == anchor, 'Public archive first-line control changed'
            matched_openings = [entry['id'] for entry in openings
                                if output[:12] == entry['indices']]
            cases.append({'page': page, 'key': item['id'],
                          'has_runes': bool(stream),
                          'first_nine_runes': ''.join(ALPHABET[i] for i in output[:9]),
                          'opening_matches': matched_openings})
    # The reversible cipher must recover an independently chosen plaintext.
    positive_plain = [LOOKUP[c] for c in 'ᛗᚩᚢᚾᛏᚪᛁᚾ']
    positive_key = keys[0]
    positive_cipher = [(p + positive_key[i % len(positive_key)]) % 29
                       for i, p in enumerate(positive_plain)]
    assert decode(positive_cipher, positive_key) == positive_plain
    return {'schema': 'liberpedia-public-wordlist-vigenere-results-v1',
            'plan_sha256': sha(HERE / 'plan.json'),
            'opening_plan_sha256': sha(openings_path),
            'source_archive_sha256': plan['source_archive_sha256'],
            'sources': sources, 'key_count': len(keys), 'page_count': 56,
            'case_count': len(cases),
            'rune_bearing_cases': sum(c['has_runes'] for c in cases),
            'opening_comparisons': sum(c['has_runes'] for c in cases) * len(openings),
            'matched_cases': sum(bool(c['opening_matches']) for c in cases),
            'positive_control': 'MOUNTAIN', 'cases': cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run()
    if args.check:
        expected = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
        if result != expected:
            raise SystemExit('Rerun differs from results.json')
    else:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: result[k] for k in ('key_count', 'page_count', 'case_count',
                                             'rune_bearing_cases', 'opening_comparisons',
                                             'matched_cases')}))


if __name__ == '__main__':
    main()
