"""Independent arithmetic check; optionally compare the pinned public output ZIP."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
LABELS = ('F', 'U', 'TH', 'O', 'R', 'C', 'G', 'W', 'H', 'N', 'I', 'J', 'EO',
          'P', 'X', 'S', 'T', 'B', 'E', 'M', 'L', 'NG', 'OE', 'D', 'A', 'AE', 'Y', 'IA', 'EA')
GRID_ROW = re.compile(r'^\s*(?:[0-9A-Za-z]{2}\s+){7}[0-9A-Za-z]{2}\s*$')


def latin_stream(chunk):
    return ''.join(''.join(re.findall(r'[A-Z]+', line))
                   for line in chunk.splitlines() if not GRID_ROW.fullmatch(line)).replace('IO', 'IA')


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
        certificate = json.loads((HERE / 'source-output-certificate.json').read_text(encoding='utf-8'))
        exact = 0
        with zipfile.ZipFile(args.source_archive) as source:
            for page in range(58):
                chunks = re.split(r'-{6,} ↑  [^\n]+  ↑ -{6,}',
                                  source.read(f'Page{page}.txt').decode('utf-8'))
                assert len(chunks) == 44, (page, len(chunks))
                path = ROOT / 'text' / f'lp2-{page:02d}.txt'
                assert hashlib.sha256(path.read_bytes()).hexdigest() == certificate['page_sha256'][f'lp2-{page:02d}']
                ciphertext = [RUNES.index(c) for c in path.read_text(encoding='utf-8') if c in RUNES]
                for key_index, key_item in enumerate(plan['keys']):
                    key = [RUNES.index(c) for c in key_item['runes']]
                    expected = ''.join(LABELS[(c - key[i % len(key)]) % 29]
                                       for i, c in enumerate(ciphertext)).replace('IO', 'IA')
                    measured = latin_stream(chunks[key_index])
                    assert expected == measured, (page, key_index + 1)
                    exact += 1
        assert exact == certificate['complete_matches'] == 58 * 43
        print(json.dumps({'archived_complete_strings_compared': exact,
                          'matching_complete_strings': exact}, ensure_ascii=False))


if __name__ == '__main__':
    main()
