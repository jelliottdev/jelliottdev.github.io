"""Independent arithmetic check; optionally compare the pinned public output ZIP."""
import argparse
import hashlib
import itertools
import json
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
LABELS = ('F', 'U', 'TH', 'O', 'R', 'C', 'G', 'W', 'H', 'N', 'I', 'J', 'EO',
          'P', 'X', 'S', 'T', 'B', 'E', 'M', 'L', 'NG', 'OE', 'D', 'A', 'AE', 'Y', 'IA', 'EA')
def archive_headings(path):
    with zipfile.ZipFile(path) as source:
        for page in range(56):
            chunks = re.split(r'-{6,} ↑  [^\n]+  ↑ -{6,}',
                              source.read(f'Page{page}.txt').decode('utf-8'))
            assert len(chunks) == 44, (page, len(chunks))
            for key_index, chunk in enumerate(chunks[:43]):
                lines = [re.sub(r'^\s*\d+\s+', '', line.strip())
                         for line in chunk.splitlines()]
                first = next((line for line in lines if line and not re.search(r'\d', line)
                              and re.search('[A-Z]', line)), '')
                yield page, key_index, re.sub('[^A-Z]', '', first.upper())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-archive', type=Path)
    args = parser.parse_args()
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    results = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    assert len(results['cases']) == 56 * 43
    assert len(results['sources']) == 56
    assert results['matched_cases'] == sum(bool(c['opening_matches']) for c in results['cases'])
    for page_number in range(56):
        path = ROOT / 'text' / f'lp2-{page_number:02d}.txt'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == results['sources'][page_number]['sha256']
        ciphertext = [RUNES.index(c) for c in path.read_text(encoding='utf-8') if c in RUNES]
        for key_index, key_item in enumerate(plan['keys']):
            case = results['cases'][page_number * 43 + key_index]
            key = [RUNES.index(c) for c in key_item['runes']]
            # A separately expressed, per-position inverse relation.
            expected = ''.join(RUNES[(ciphertext[i] + 29 - key[i % len(key)]) % 29]
                               for i in range(min(9, len(ciphertext))))
            assert case['first_nine_runes'] == expected
    print('PASS: all 2,408 stored prefixes match independently recomputed GP subtraction')
    if args.source_archive:
        assert hashlib.sha256(args.source_archive.read_bytes()).hexdigest() == plan['source_archive_sha256']
        exact = partial = 0
        mismatches = []
        for page, key, heading in archive_headings(args.source_archive):
            measured = results['cases'][page * 43 + key]['first_nine_runes']
            if not measured and not heading:
                continue
            # The archived output uses both IO and IA for the same GP rune.
            alternatives = [('IA', 'IO') if rune == 'ᛡ' else (LABELS[RUNES.index(rune)],)
                            for rune in measured]
            candidates = [''.join(parts) for parts in itertools.product(*alternatives)]
            partial += 1
            if any(heading.startswith(candidate) or candidate.startswith(heading)
                   for candidate in candidates):
                exact += 1
            elif len(mismatches) < 10:
                transliteration = candidates[0]
                n = min(len(heading), len(transliteration))
                mismatches.append({'page': page, 'key': key + 1,
                                   'archive': heading[:n], 'replay': transliteration[:n]})
        print(json.dumps({'archived_headings_compared': partial,
                          'matching_prefixes': exact, 'first_mismatches': mismatches},
                         ensure_ascii=False))
        assert partial == 55 * 43 and exact == partial, 'Archived first lines diverge'


if __name__ == '__main__':
    main()
