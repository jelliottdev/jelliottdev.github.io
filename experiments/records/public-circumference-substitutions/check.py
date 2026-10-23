"""Independent map check and optional comparison to both archived outputs."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
          53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109)
LABELS = ('F', 'U', 'TH', 'O', 'R', 'C', 'G', 'W', 'H', 'N', 'I', 'J', 'EO',
          'P', 'X', 'S', 'T', 'B', 'E', 'M', 'L', 'NG', 'OE', 'D', 'A', 'AE', 'Y', 'IA', 'EA')


GRID_ROW = re.compile(r'^\s*(?:[0-9A-Za-z]{2}\s+){7}[0-9A-Za-z]{2}\s*$')


def latin_stream(chunk):
    return ''.join(''.join(re.findall(r'[A-Z]+', line))
                   for line in chunk.splitlines() if not GRID_ROW.fullmatch(line)).replace('IO', 'IA')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-directory', type=Path)
    args = parser.parse_args()
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    assert len(result['pages']) == 56
    for radius, radii in (('index', range(29)), ('prime', PRIMES)):
        for rounding in ('nearest', 'truncate'):
            name = f'{radius}-{rounding}'
            # None of these products falls exactly halfway between integers.
            operation = (lambda x: math.floor(x + 0.5)) if rounding == 'nearest' else math.floor
            table = [operation(2 * math.pi * r) % 29 for r in radii]
            assert table == result['maps'][name]['output_indices']
            assert len(set(table)) == result['maps'][name]['distinct_outputs']
            for entry in result['pages']:
                source = ROOT / 'text' / (entry['page'] + '.txt')
                raw = source.read_text(encoding='utf-8')
                assert hashlib.sha256(source.read_bytes()).hexdigest() == entry['input_sha256']
                transformed = ''.join(RUNES[table[RUNES.index(c)]] if c in RUNES else c
                                      for c in raw)
                assert hashlib.sha256(transformed.encode()).hexdigest() == entry['outputs'][name]['output_sha256']
    print('PASS: four maps, all 56 page hashes, and per-page output digests reproduce')
    if args.source_directory:
        certificate = json.loads((HERE / 'source-output-certificate.json').read_text(encoding='utf-8'))
        for radius, source in zip(('index', 'prime'), plan['source_outputs']):
            path = args.source_directory / Path(source['path']).name
            lf_bytes = path.read_bytes().replace(b'\r\n', b'\n')
            assert hashlib.sha256(lf_bytes).hexdigest() == certificate['variants'][radius]['source_git_lf_sha256']
            assert hashlib.sha256(lf_bytes.replace(b'\n', b'\r\n')).hexdigest() == source['sha256']
            chunks = re.split(r'-{6,} ↓  Page \d+  ↓ -{6,}', lf_bytes.decode('utf-8'))
            assert len(chunks) == 58
            table = [math.floor(2 * math.pi * r) % 29
                     for r in (range(29) if radius == 'index' else PRIMES)]
            matching = 0
            for page in range(57):
                input_path = ROOT / 'text' / f'lp2-{page:02d}.txt'
                assert hashlib.sha256(input_path.read_bytes()).hexdigest() == certificate['page_sha256'][f'lp2-{page:02d}']
                ciphertext = [RUNES.index(c) for c in input_path.read_text(encoding='utf-8') if c in RUNES]
                expected = ''.join(LABELS[table[c]] for c in ciphertext).replace('IO', 'IA')
                assert expected == latin_stream(chunks[page + 1]), (radius, page)
                matching += 1
            assert matching == certificate['variants'][radius]['complete_matches'] == 57
            print(json.dumps({'radius': radius, 'archived_complete_strings_compared': matching,
                              'matching_complete_strings': matching}))


if __name__ == '__main__':
    main()
